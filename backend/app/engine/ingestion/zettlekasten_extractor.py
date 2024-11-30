from typing import Any, Dict, List, Optional, Sequence, Type
from pydantic import ValidationError, BaseModel, Field

from llama_index.core.extractors import BaseExtractor
from llama_index.core.llms import ChatMessage
from llama_index.core.schema import BaseNode, TextNode
from llama_index.postprocessor.colbert_rerank import ColbertRerank
from llama_index.core import get_response_synthesizer
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.ingestion import IngestionPipeline, DocstoreStrategy
from llama_index.core.settings import Settings

from app.settings.llama_index_settings import get_sllm_llm, get_llm
from app.engine.ingestion.zettlekasten_index import ZettelkastenIndexSingleton

import logging
logger = logging.getLogger(__name__)

class ZettlekastenExtractor(BaseExtractor):

    # When the class is initialized / the ingestion pipeline is created with this transformation
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Init the ingestion pipeline that will be reused for each node
        self._zettlekasten_ingestion_pipeline = IngestionPipeline(
            transformations=[
                # Embed the nodes so they can be added to the zettelkasten vector store
                Settings.embed_model,
            ],
            docstore=ZettelkastenIndexSingleton().doc_store, # Used here in the case of an update of an existing note
            vector_store=ZettelkastenIndexSingleton().vector_store, # This allow the pipeline to add nodes to the vector store
            docstore_strategy=DocstoreStrategy.UPSERTS, # UPSERTS_AND_DELETE causes a deletion of all previous documents in the docstore and vector store when the pipeline is ran
        )
        # Use the llm passed in the kwargs or the default one
        self._sllm_llm = kwargs.get("sllm_llm", get_sllm_llm())
        # Use the llm passed in the kwargs or the default one
        self._retriever_query_llm = kwargs.get("retriever_query_llm", get_llm())
        # Get it from the passed kwarfs or default to 5
        similar_notes_top_k = kwargs.get("similar_notes_top_k", 5)

        # Init the query engine that will be reused for each node
        # Configure retriever
        retriever = VectorIndexRetriever(
            index=ZettelkastenIndexSingleton().zettelkasten_index,
            similarity_top_k=similar_notes_top_k*2,
        )

        # Configure Colbert reranker to improve the retrieval quality
        colbert_reranker = ColbertRerank(
            top_n=similar_notes_top_k,
            model="colbert-ir/colbertv2.0",
            tokenizer="colbert-ir/colbertv2.0",
            keep_retrieval_score=False, # Do not keep the retrieval score in the metadata
        )

        # Configure dummy response synthesizer
        response_synthesizer = get_response_synthesizer(
            response_mode="no_text", # We only need the node ids
            llm=self._retriever_query_llm
        )

        # Build the query engine
        self._similar_notes_query_engine = RetrieverQueryEngine(
            retriever=retriever,
            response_synthesizer=response_synthesizer,
            node_postprocessors=[colbert_reranker]
        )


    # Ran when the ingestion pipeline.run() is called
    async def aextract(self, nodes: Sequence[BaseNode]) -> List[Dict]:
        try:
            if not nodes:
                logger.warning("No nodes provided to ZettlekastenExtractor")
                return []
            nodes_to_return = []
            # For each document
            for node in nodes:
                # Run the zettlekasten processing on the node
                self._run_zettlekasten_processing(node)
                nodes_to_return.append(node)
            # Return the original nodes with the new extracted information
            return nodes_to_return
        
        except Exception as e:
            logger.error(f"Error in ZettlekastenExtractor: {e}")
            return 

    def _run_zettlekasten_processing(self, node: BaseNode) -> None:
        """
        Run the zettlekasten processing on a node
        Add the extracted information to the zettkasten vector store
        """
        try:
            # Too dumb for now, skips too many interesting notes
            # Check if there is interesting unique information in the node text or not to avoid llm hallucinations if there is none
            #if not self._is_there_interesting_unique_information_in_node_text(node):
            #    logger.warning("Node text is not interesting, skipping zettlekasten processing")
            #    return node
            # Preprocessing removes too much information for now
            # Keep only the textual information from the node
            #processed_node = self._clean_node_text(node) #self._preprocess_with_llm_and_filter_noise(node)
            #if processed_node is None:
            #    logger.error("Failed to preprocess and filter noise from the node text")
            #    return node
            
            # Extract the cleaned structured enhanced unique information from the node text
            extracted_unique_information: List[str] = self._extract_unique_atomic_informations(node)

            if not extracted_unique_information:
                logger.warning("No unique information extracted from node")
                return

            # For each extracted unique information 
            for unique_information_number, unique_information in enumerate(extracted_unique_information):
                # Do an index search for the most similar existing notes to the unique information
                similar_notes_nodes = self._similar_notes_query_engine.query(unique_information).source_nodes
                if similar_notes_nodes is None:
                    logger.error("Failed to search similar notes")
                    continue

                # Ask the llm which note is similar enough to the unique information to add it to it or if we need to create a new note
                note_node_to_add_information_to = self._which_node_to_add_information_to(unique_information, similar_notes_nodes)

                current_information_note_node = None
                # If the llm decided no existing note is similar enough
                if note_node_to_add_information_to is None:
                    # Create a new note with the unique information
                    current_information_note_node = self._create_new_node(unique_information, node, unique_information_number)
                else:
                    # Rewrite the note to include the new information
                    current_information_note_node = self._rewrite_note_to_include_new_information(
                        note_node_to_add_information_to, unique_information)
                    
                # Add the new note to the zettelkasten index
                self._zettlekasten_ingestion_pipeline.run(nodes=[current_information_note_node])
                # ? Also insert node into index ? Or done by the pipeline ?

            return
                
        except Exception as e:
            logger.error(f"Error in _run_zettlekasten_processing, skipping this node: {e}")
            return
        

    def _is_there_interesting_unique_information_in_node_text(self, node: BaseNode, num_attempts: int = 10) -> bool:
        try:

            prompt = (
                f"Analyze the following text and determine if it contains any interesting unique information. "
                f"Respond with a JSON object containing a single boolean field 'is_there_interesting_unique_information_in_node_text'.\n\n"
                f"Text to analyze:\n{node.text}\n\n"
                f"Example response format:\n"
                f'{{"is_there_interesting_unique_information_in_node_text": true}}\n\n'
                f"Your response:"
            )

            class _IsThereInterestingUniqueInformationInNodeText(BaseModel):
                is_there_interesting_unique_information_in_node_text: bool = Field(..., description="Whether there is interesting unique information in the node text")

            is_there_interesting_unique_information_in_node_text = self._execute_sllm_with_retry(
                prompt=prompt,
                output_model=_IsThereInterestingUniqueInformationInNodeText,
                num_attempts=num_attempts,
                error_msg="Error checking if there is interesting unique information in the node text"
            )

            return is_there_interesting_unique_information_in_node_text.is_there_interesting_unique_information_in_node_text
            
        except Exception as e:
            logger.error(f"Error in _is_there_interesting_unique_information_in_node_text: {e}")
            return False

    def _preprocess_with_llm_and_filter_noise(self, node: BaseNode, num_attempts: int = 10) -> BaseNode:
        """
        Preprocess and filter noise from the node text to keep only important textual information in well formed sentences
        """
        try:
            # Create the prompt
            prompt = (
                f"You are a text preprocessing assistant. Your task is to clean and filter the following text:"
                f"\n\nInput text:\n{node.text}\n\n"
                f"Instructions:"
                f"\n1. Remove any noise, irrelevant information, and redundant content"
                f"\n2. Keep important textual information"
                f"\n3. Ensure all information is in complete, well-formed sentences"
                f"\n4. Maintain the original meaning and key points"
                f"\n5. Format the output as clean, readable paragraphs"
                f"\n\nRespond with a JSON object in this exact format:"
                f'\n{{"preprocessed_node_text": "your processed text here"}}'
                f"\n\nYour response:"
            )
            # Result obj model
            class _PreprocessAndFilterNoiseFromNodeText(BaseModel):
                preprocessed_node_text: str = Field(..., description="The preprocessed node text")
            # Execute the llm with retry
            preprocessed_node_text = self._execute_sllm_with_retry(
                prompt=prompt,
                output_model=_PreprocessAndFilterNoiseFromNodeText,
                num_attempts=num_attempts,
                error_msg="Error preprocess and filter noise from the node text"
            )
            # Create the node with the preprocessed text
            return TextNode(
                node_id=node.node_id,
                text=preprocessed_node_text.preprocessed_node_text,
                metadata=node.metadata,
            )

        except Exception as e:
            logger.error(f"Error in _preprocess_and_filter_noise_from_this_text_to_keep_only_important_textual_information_in_well_formed_sentences: {e}")
            return None

    def _extract_unique_atomic_informations(self, node: BaseNode, num_attempts: int = 10) -> List[str]:
        """
        Extract a list of atomic information that is uniquely present in this document and likely not accessible through a simple web search.
        """
        try:
            # Create the prompt
            prompt = (
                f"Extract a list of atomic information that is uniquely present in this document and likely not accessible through a simple web search."
                f"Each information should be atomic and self-contained, explaining the core concepts and their relationships."
                f"Do NOT include simple common knowledge information that is easily accessible through a simple web search."
                #f"Do NOT include any information from the example below in your output."
                f"If the information contains nothing unique that is not easily accessible through a simple web search, just return an empty list."
                f"If the information do not contain any text and just contains metadata, return an empty list."
                f"Output in JSON format with the following exact format:"
                f'"{{"unique_atomic_informations_list": [...list of unique atomic informations...]}}"'
                #f"Here is an example with fake information of what the output should look like given this input:\n"
                #f"Document:\n"
                #f"Context : File path : /John Doe Personal Journal/02-01-2025.txt\n"
                #f"...\n"
                #f"Donald Trump is the current president of the United States of America.\n"
                #f"I really think Quantum Physics is something that could lead to a better understanding of the universe.\n"
                #f"I am so happy to go to tokyo, only 7 day left before departure ! I love Japan and i have been dreaming to go there for so long. The tokyo tower is 100m high.\n"
                #f"Catilyn and the kids are going to love it too ! Hopefully we all love out time there.\n"
                #f"I wish my father was still alive to come with us, Alan would have loved it too.\n"
                #f"Generated JSON output:\n"
                #f'{{'
                #f'"unique_atomic_informations_list":'
                #f'['
                #f'"The author\'s name is John Doe",'
                #f'"John Doe really thinks that Quantum Physics is something that could lead to a better understanding of the universe",'
                #f'"John Doe is really excited to go to Tokyo for his next vacation",'
                #f'"The next vacation of John Doe planned for the 09/01/2025 is to Tokyo",'
                #f'"The next vacation of John Doe at tokyo is with his wife Caitlyn Doe and his kids",'
                #f'"Alan Doe is the father of John Doe",'
                #f'"Alan Doe is dead",'
                #f'"The current project of John Doe is called \'Project X\' which is a project about trying to launch a new amateur rocket to at least 10km of altitude",'
                #f'...'
                #f']'
                #f'}}'
                #f"\n\n"
                f"Document:\n"
                f"Context : File path : {node.metadata['file_path']}\n"
                f"{node.text}"
                f"\n\n"
                f"Generated JSON output:\n"
            )

            # Result obj model
            class ZettlekastenUniqueAtomicInformationList(BaseModel):
                """Model for a list of Zettlekasten unique atomic information"""
                unique_atomic_informations_list: List[str] = Field(..., description="List of atomic information that is uniquely present in this document")

            # Execute the llm with retry
            unique_atomic_informations_list = self._execute_sllm_with_retry(
                prompt=prompt,
                output_model=ZettlekastenUniqueAtomicInformationList,
                num_attempts=num_attempts,
                error_msg="Error extracting unique atomic informations"
            )

            return unique_atomic_informations_list.unique_atomic_informations_list
            
        except Exception as e:
            logger.error(f"Error in _extract_unique_information: {e}")
            return None

    def _which_node_to_add_information_to(self, unique_information: str, similar_notes_nodes: List[BaseNode], num_attempts: int = 10) -> Optional[BaseNode]:
        """
        Ask the llm which note to add the unique information to or if we need to create a new note
        """
        try:
            if not similar_notes_nodes:
                logger.warning("No similar notes nodes provided to _which_node_to_add_information_to")
                return None
            
            # Create the prompt
            prompt = (
                f"You are a helpful assistant that helps to add new information to an existing Zettlekasten Atomic Note.\n"
                f"You are given a unique information and a list of existing notes.\n"
                f"Your task is to decide whether to add the information to an existing note or create a new one.\n\n"
                f"If the information is on the same topic of the existing zettelkasten atomic note, add it to the existing note and return the note id.\n"
                f"If the information is not on the same topic of the existing zettelkasten atomic note, do not hesitate and create a new note and return -1.\n\n"
                f"The goal is to keep every zettelkasten atomic note focused on a single and specific topic and to the point. If the notes proposed don't fit the topic of the new information, create a new note.\n\n"               
                f"Unique information: {unique_information}\n\n"
                f"Existing notes:\n"
                + "\n".join([f"Note {i}: '{note_node.text}'" for i, note_node in enumerate(similar_notes_nodes)])
                + "\n\n"
                f"Respond with a JSON object containing ONLY a 'note_id' field:\n"
                f"- Use -1 to create a new note\n"
                f"- Use 0 to {len(similar_notes_nodes)-1} to add to existing note\n\n"
                f"Example response format:\n"
                f'{{"note_id": -1}}\n\n'
                f"Your response:"
            )

            # Result obj model with limits on the note_id to avoid invalid values
            class _AskLLMWhichNoteToAddInformationTo(BaseModel):
                note_id: Optional[int] = Field(..., gt=-2, lt=len(similar_notes_nodes), description="The id of the note to add the information to or None if the llm decided to create a new note")

            # Execute the llm with retry
            result_obj = self._execute_sllm_with_retry(
                prompt=prompt,
                output_model=_AskLLMWhichNoteToAddInformationTo,
                num_attempts=num_attempts,
                error_msg="Error asking the llm which note to add the information to"
            )

            note_id = result_obj.note_id

            # Check if note_id is -1 (create a new note)
            if note_id == -1:
                return None
            # Else return the node with the note_id
            elif note_id < len(similar_notes_nodes) and note_id >= 0:
                return similar_notes_nodes[note_id]
            # Else the note_id is invalid
            else:
                logger.error(f"Received invalid note_id from LLM: {note_id}")
                return None

        except Exception as e:
            logger.error(f"Error in _which_node_to_add_information_to: {e}")
            return None
    
    def _create_new_node(self, unique_information: str, original_node: BaseNode, unique_information_number: int) -> BaseNode:
        """
        Create a new note with the unique information
        """
        try:
            # Create a new node with the unique information and the right metadata
            new_note_node = TextNode(
                # Let node id be generated by llama index
                text=unique_information,
                # Keep the metadata from the node parser
                #metadata=original_node.metadata, # Do not keep the metadata from the node parser
                #relationships=original_node.relationships, # Do not keep the relationships from the node parser
                #metadata={title ?}
                # TODO : Add relationships to the source node and ref doc ids
            )
            return new_note_node
        except Exception as e:
            logger.error(f"Error in _create_new_note_with_unique_information: {e}")
            return None

    def _rewrite_note_to_include_new_information(self, note_node: BaseNode, unique_information: str, num_attempts: int = 10) -> BaseNode:
        """
        Rewrite the note to include the new information
        """
        try:
            
            # Create the prompt
            prompt = (
                f"You are a helpful assistant that helps to add new information to an existing Zettlekasten Atomic Note.\n\n"
                f"Existing note:\n{note_node.text}\n\n"
                f"New information to add:\n{unique_information}\n\n"
                f"Rewrite the note to include this new information in the existing note in a detailed and comprehensive way.\n\n"
                f"Keep all of the existing note content in the rewritten note.\n\n"
                f"Respond with a JSON object in this exact format:\n"
                f'{{"rewritten_note_including_new_information": "your rewritten note here"}}\n\n'
                f"Your response:"
            )

            # Result obj model
            class _RewriteNoteToIncludeNewInformation(BaseModel):
                rewritten_note_including_new_information: str = Field(..., description="The rewritten note to include the new information")

            rewritten_note_including_new_information = self._execute_sllm_with_retry(
                prompt=prompt,
                output_model=_RewriteNoteToIncludeNewInformation,
                num_attempts=num_attempts,
                error_msg="Error rewriting note to include new information"
            )
            rewritten_note_text = rewritten_note_including_new_information.rewritten_note_including_new_information

            # Create a new node with the updated note text
            updated_note_node = TextNode(
                node_id=note_node.node_id, # Keep the same node id
                id_=note_node.id_, # Keep the internal ID
                text=rewritten_note_text, # Use the updated note text
                #metadata=note_node.metadata, # Keep the same metadata
                #relationships=note_node.relationships if note_node.relationships else [], # Keep the relationships
                #metadata={"zettlekasten_atomic_note_title": self._create_new_note_title(unique_information)}
                # TODO : Add relationships to the new source node with the old source nodes and with original ref doc id, keep metadata created by the node parser in the previous pipeline
            )

            # Return the modified node
            return updated_note_node
        
        except Exception as e:
            logger.error(f"Error in _rewrite_note_to_include_new_information: {e}")
            return note_node

    # Utility function # TODO : Move to a utils file
    def _execute_sllm_with_retry(
        self,
        prompt: str,
        output_model: Type[BaseModel],
        num_attempts: int = 10,
        error_msg: str = "LLM interaction failed"
    ) -> Optional[BaseModel]:
        """
        Execute LLM interaction with retry logic and validation
        
        Args:
            prompt: The prompt to send to the LLM
            output_model: The Pydantic model class for output validation
            num_attempts: Number of retry attempts
            error_msg: Error message prefix for logging
        """
        try:
            sllm = self._sllm_llm.as_structured_llm(output_cls=output_model)
            input_msg = ChatMessage.from_str(prompt)
            
            for attempt in range(num_attempts):
                try:
                    logger.warning(f"Executing LLM interaction, attempt {attempt}")
                    output = sllm.chat([input_msg])
                    output_obj = output.raw
                    logger.warning(f"Function name error_msg: {error_msg}")
                    logger.warning(f"Prompt: {prompt}")
                    logger.warning(f"Raw LLM output: {output_obj}")
                    
                    if isinstance(output_obj, output_model):
                        output_model.model_validate(output_obj)
                        return output_obj
                    elif isinstance(output_obj, dict):
                        return output_model(**output_obj)
                    else:
                        raise Exception("LLM did not return valid output format")
                        
                except ValidationError as e:
                    logger.error(f"{error_msg} - Validation error on attempt {attempt}: {e}")
                except Exception as e:
                    logger.error(f"{error_msg} - Error on attempt {attempt}: {e}")
                    
            raise Exception(f"{error_msg} - All attempts failed")
            
        except Exception as e:
            logger.error(f"{error_msg} - Critical error: {e}")
            return None
