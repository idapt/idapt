from typing import Dict, List
from pydantic import ValidationError

from llama_index.core.extractors import BaseExtractor
from llama_index.core.llms import ChatMessage

from app.settings.app_settings import AppSettings
from app.settings.llama_index_settings import get_integrated_ollama_sllm, get_custom_ollama_sllm
from backend.app.engine.ingestion.types import ZettlekastenNoteTitleList, ZettlekastenNote

import logging
logger = logging.getLogger(__name__)

class ZettlekastenExtractor(BaseExtractor):

    def _extract_titles(self, content: str, num_attempts: int = 10) -> List[str]:
        try:
            # Create the structured LLM with the output ZettlekastenNoteTitleList pydantic object
            if AppSettings.model_provider == "custom_ollama":
                sllm = get_custom_ollama_sllm().as_structured_llm(output_cls=ZettlekastenNoteTitleList)
            else:
                sllm = get_integrated_ollama_sllm().as_structured_llm(output_cls=ZettlekastenNoteTitleList)

            # Create the prompt
            prompt = (
                "Extract a list of potential Titles for Zettlekasten Atomic Notes from the following Journaling Entry. "
                #"The output should be a JSON object with a \"titles\" array containing strings.\n\n"
                f"Journaling Entry:\n{content}\n\n"
                #"Expected JSON format:\n{\"titles\": [\"Title 1\", \"Title 2\", ...]}\n\n"
                "Generated JSON:"
            )

            input_msg = ChatMessage.from_str(prompt)
            
            # Try to generate the titles
            for attempt in range(num_attempts):
                try:
                    logger.info(f"Generating titles with LLM, attempt {attempt}")
                    # Generate the titles using the LLM
                    output = sllm.chat([input_msg])
                    # Get the structured output pydantic object
                    output_obj = output.raw

                    # Validate the output
                    if isinstance(output_obj, ZettlekastenNoteTitleList):
                        ZettlekastenNoteTitleList.model_validate(output_obj)
                    else:
                        raise Exception("LLM did not return a ZettlekastenNoteTitleList object")

                    return output_obj.titles

                except ValidationError as e:
                    logger.error(f"Invalid output from LLM, retrying...")
                    continue

                except Exception as e:
                    logger.error(f"Error generating titles with LLM, attempt {attempt}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error extracting titles: {e}")
            return []

    def _extract_note(self, title: str, content: str, num_attempts_per_note: int = 10) -> ZettlekastenNote:
        try:
            #if similar_note:
            #    prompt = (
            #        f"Rewrite the following Zettlekasten Existing Atomic Note strictly on the subject of the Title, gather all new relevant information on the subject from the New #Content.\n\n"
            #        f"Title:\n{title}\n\n"
            #        f"Zettlekasten Existing Atomic Note:\n{similar_note}\n\n"
            #        f"New Content:\n{content}\n\n"
            #        f"JSON Schema to fill:\n{note_json_schema}\n\n"
            #        f"Filled JSON Schema:\n"
            #    )
            #else:

            # Create the structured LLM with the output ZettlekastenNote pydantic object
            if AppSettings.model_provider == "custom_ollama":
                sllm = get_integrated_ollama_sllm().as_structured_llm(output_cls=ZettlekastenNote)
            else:
                sllm = get_integrated_ollama_sllm().as_structured_llm(output_cls=ZettlekastenNote)

            prompt = (
                f"Create a comprehensive Zettlekasten Atomic Note that deeply explores the subject of the Title. "
                f"Extract and synthesize ALL relevant information from the Content that relates to this topic. "
                f"The note should be detailed and self-contained, explaining the core concepts and their relationships. "
                f"Include specific examples and insights from the Content when relevant.\n\n"
                f"Title:\n{title}\n\n"
                f"Content:\n{content}\n\n"
                f"Fill the following schema with your comprehensive note:\n"
                f"- zettlekasten_atomic_note_title: The given title\n"
                f"- zettlekasten_atomic_note_markdown_content_strictly_about_title: A detailed exploration of the topic\n"
                f"- questions_this_note_answers: Key questions this note addresses (at least 3)\n"
                f"- tags_keywords_this_note_is_about: Important concepts and themes (at least 4)\n\n"
                f"Generated Note:"
            )

            #print(f"Prompt:\n{prompt}")

            # Create the input message
            input_msg = ChatMessage.from_str(prompt)
            
            for attempt in range(num_attempts_per_note):
                try:
                    logger.info(f"Generating note for title: {title} with LLM, attempt {attempt}")
                    # Generate the note using the LLM
                    output = sllm.chat([input_msg])
                    #print(f"Output:\n{output}")

                    # Get the structured output pydantic object
                    output_obj = output.raw

                    # Validate the output
                    if isinstance(output_obj, ZettlekastenNote):
                        ZettlekastenNote.model_validate(output_obj)
                    else:
                        raise Exception("LLM did not return a ZettlekastenNote object")

                    return output_obj
                    
                except ValidationError as e:
                    logger.error(f"Invalid output from LLM for note {title}, attempt {attempt}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error generating note for title: {title} with LLM, attempt {attempt}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error in _extract_note: {e}")
            return None


    def _separate_nodes_by_ref_id(self, nodes) -> Dict:
        try:
            separated_items = {}

            for node in nodes:
                key = node.ref_doc_id
                if key not in separated_items:
                    separated_items[key] = []
                separated_items[key].append(node)

            return separated_items
        except Exception as e:
            logger.error(f"Error in _separate_nodes_by_ref_id: {e}")
            return {}
            


    async def aextract(self, nodes) -> List[Dict]:
        try:
            if not nodes:
                logger.warning("No nodes provided to ZettlekastenExtractor")
                return []

            nodes_by_doc_id = self._separate_nodes_by_ref_id(nodes)
            # Dict of list of notes for each document access by document id
            #notes_list_by_doc_id = {}
            # A special dict to store the json dump of the notes for each document for metadata addition at the end
            notes_json_list_by_doc_id = {}
            # For each document
            for key, nodes in nodes_by_doc_id.items():
                # For each node of this document
                for node in nodes:
                    # Extract the titles for this node content
                    titles = self._extract_titles(node.text)

                    # For each title extracted
                    for title in titles:
                        #similar_notes_info = None #await self.search_similar_notes(title)
                        #if similar_notes_info:
                        #    similar_notes = similar_notes_info.get("similar_notes", [])
                        #    similarity_score = similar_notes_info.get("similarity_score", 0)
                        #
                        #    if similarity_score >= self.similarity_threshold and similar_notes:
                        #        similar_note = similar_notes[0]
                        #        note = await self.update_or_create_note(title, content, similar_note)
                        #    else:
                        #        note = await self.update_or_create_note(title, content)
                        #else:
                        # Create a zettlekasten note for this title
                        note = self._extract_note(title, node.text)
                        if note:
                            # Add the note to the list of notes for this document
                            #notes_list_by_doc_id[key].append(note)
                            # Add the note to the list of json dumps for this document
                            if key not in notes_json_list_by_doc_id:
                                notes_json_list_by_doc_id[key] = []
                            notes_json_list_by_doc_id[key].append(note.model_dump_json())
                        else:
                            logger.error(f"Error in _extract_note for title: {title}, skipping this note")

            # Return the new extracted metadata as a list of zettlekasten note json objects strings                        
            return [{"document_zettlekasten_notes": notes_json_list_by_doc_id[node.ref_doc_id]} for node in nodes]

        except Exception as e:
            logger.error(f"Error in ZettlekastenExtractor: {e}")
            return []
