from sqlalchemy.orm import Session
from app.database.models import Datasource, ProcessingStack, ProcessingStep, ProcessingStackStep
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.extractors import (
    TitleExtractor,
    QuestionsAnsweredExtractor,
    SummaryExtractor,
    KeywordExtractor,
)

from pydantic import BaseModel, Field
import logging
import re

from app.settings.model_initialization import init_embedding_model
from app.constants.file_extensions import TEXT_FILE_EXTENSIONS

logger = logging.getLogger("uvicorn")

def create_default_processing_stacks(session: Session):
    """Create default processing stacks in the database"""
    try:
        # Create processing steps
        # Sentence splitter step
        create_processing_step(session=session, type="node_parser", identifier="sentence_splitter", display_name="Sentence Splitter", description="Splits text into sentences with configurable chunk size and overlap", parameters_schema=SentenceSplitterParameters.model_json_schema())
        # Embedding step
        create_processing_step(session=session, type="embedding", identifier="embedding", display_name="Embedding", description="Converts text into vector embeddings for semantic search", parameters_schema={})


        # Text Processing
        # Try to get the stack from the database
        text_processing_stack = session.query(ProcessingStack).filter(ProcessingStack.identifier == "text_processing").first()
        if text_processing_stack:
            logger.info(f"Text processing stack already exists: {text_processing_stack.display_name}")
            return
        # Text Processing
        create_empty_processing_stack(
            session=session,
            stack_identifier="text_processing",
            display_name="Text Processing",
            description="Processing stack for text data",
            supported_extensions=list(TEXT_FILE_EXTENSIONS)
        )
        # Add processing stack steps to it 
        sentence_splitter_parameters = SentenceSplitterParameters(
            chunk_size=512,
            chunk_overlap=128
        )
        add_processing_stack_step(session=session, stack_identifier="text_processing", step_identifier="sentence_splitter", order=1, parameters=sentence_splitter_parameters.model_dump())
        add_processing_stack_step(session=session, stack_identifier="text_processing", step_identifier="embedding", order=2, parameters={})

        # TODO Add image, video, audio, code processing stacks

        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating default processing stacks: {e}")
        raise e
    
class SentenceSplitterParameters(BaseModel):
    chunk_size: int = Field(description="The size of the chunks to split the text into", default=512)
    chunk_overlap: int = Field(description="The overlap of the chunks to split the text into", default=128)

def create_processing_step(session: Session, type: str, identifier: str, display_name: str, description: str, parameters_schema: dict):
    """Create a processing step in the database"""
    try:
        # Check if the processing step already exists
        existing_step = session.query(ProcessingStep).filter(ProcessingStep.identifier == identifier).first()
        if existing_step:
            raise ValueError(f"Processing step with identifier '{identifier}' already exists")
        
        session.add(ProcessingStep(type=type, identifier=identifier, display_name=display_name, description=description, parameters_schema=parameters_schema))
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating processing step: {e}")
        raise e

def create_empty_processing_stack(
    session: Session, 
    stack_identifier: str, 
    display_name: str, 
    description: str,
    supported_extensions: list[str] | None = None
):
    """Create an empty processing stack in the database"""
    try:
        existing_stack = session.query(ProcessingStack).filter(ProcessingStack.identifier == stack_identifier).first()
        if existing_stack:
            raise ValueError(f"Processing stack with identifier '{stack_identifier}' already exists")

        session.add(ProcessingStack(
            identifier=stack_identifier, 
            display_name=display_name, 
            description=description,
            supported_extensions=supported_extensions
        ))
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating empty processing stack: {e}")
        raise e
    
def get_default_parameters(parameters_schema: dict) -> dict:
    """Extract default values from a parameters schema"""
    default_params = {}
    if 'properties' in parameters_schema:
        for prop_name, prop_schema in parameters_schema['properties'].items():
            if 'default' in prop_schema:
                default_params[prop_name] = prop_schema['default']
    return default_params

def add_processing_stack_step(session: Session, stack_identifier: str, step_identifier: str, order: int, parameters: dict | None = None):
    """Add a processing stack step to a processing stack in the database"""
    try:
        # Get the step to access its schema
        step = session.query(ProcessingStep).filter_by(identifier=step_identifier).first()
        if not step:
            raise ValueError(f"Step not found: {step_identifier}")

        # Get default parameters from schema
        default_params = get_default_parameters(step.parameters_schema)
        
        # Merge provided parameters with defaults
        final_parameters = {**default_params, **(parameters or {})}

        session.add(ProcessingStackStep(
            stack_identifier=stack_identifier, 
            step_identifier=step_identifier, 
            order=order, 
            parameters=final_parameters
        ))
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error adding processing stack step: {e}")
        raise e
    
def delete_processing_stack_step(session: Session, stack_identifier: str, step_identifier: str):
    """Delete a processing stack step from the database"""
    try:
        session.query(ProcessingStackStep).filter_by(stack_identifier=stack_identifier, step_identifier=step_identifier).delete()
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting processing stack step: {e}")
        raise e

def change_processing_stack_step_order(session: Session, stack_identifier: str, step_identifier: str, new_order: int):
    """Change the order of a processing stack step in the database"""
    try:
        # Get the step to move and its current order
        step_to_move = session.query(ProcessingStackStep).filter_by(
            stack_identifier=stack_identifier,
            step_identifier=step_identifier
        ).first()
        
        if not step_to_move:
            raise ValueError(f"Step not found: {step_identifier}")
            
        current_order = step_to_move.order
        
        # If the order hasn't changed, do nothing
        if current_order == new_order:
            return
            
        # Get all other steps for the stack
        other_steps = session.query(ProcessingStackStep).filter_by(
            stack_identifier=stack_identifier
        ).filter(
            ProcessingStackStep.step_identifier != step_identifier
        ).all()
        
        # Update orders
        if new_order > current_order:
            # Moving down - decrease order of steps in between
            for step in other_steps:
                if current_order < step.order <= new_order:
                    step.order -= 1
        else:
            # Moving up - increase order of steps in between
            for step in other_steps:
                if new_order <= step.order < current_order:
                    step.order += 1
                    
        # Set new order for the moved step
        step_to_move.order = new_order
        
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error changing processing stack step order: {e}")
        raise e

def get_transformer_for_step(step: ProcessingStep, parameters: dict, datasource: Datasource):
    """Convert a ProcessingStep and parameters into a LlamaIndex transformer"""
    try:
        match step.identifier:
            case "sentence_splitter":
                return SentenceSplitter(**parameters)
            case "embedding":
                return init_embedding_model(datasource.embedding_provider, datasource.embedding_settings)
            case "title_extractor":
                return TitleExtractor(**parameters)
            case "questions_extractor":
                return QuestionsAnsweredExtractor(**parameters)
            case "summary_extractor":
                return SummaryExtractor(**parameters)
            case "keyword_extractor":
                return KeywordExtractor(**parameters)
      
        raise ValueError(f"Unknown step type: {step.type} with identifier: {step.identifier}")
    except Exception as e:
        logger.error(f"Error getting transformer for step: {e}")
        raise e

def get_transformations_for_stack(session: Session, stack_identifier: str, datasource: Datasource):
    """Get all transformations for a processing stack"""
    try:
        stack = session.query(ProcessingStack).filter_by(identifier=stack_identifier).first()
        if not stack:
            raise ValueError(f"Stack not found: {stack_identifier}")
          
        transformations = []
        stack_steps = (session.query(ProcessingStackStep)
                      .filter_by(stack_identifier=stack_identifier)
                      .order_by(ProcessingStackStep.order)
                      .all())
                      
        for stack_step in stack_steps:
            transformer = get_transformer_for_step(stack_step.step, stack_step.parameters or {}, datasource)
            transformations.append(transformer)
            
        return transformations
    except Exception as e:
        logger.error(f"Error getting transformations for stack: {e}")
        raise e

def generate_stack_identifier(name: str) -> str:
    """Generate a safe identifier from a stack name"""
    try:
        # TODO Add duplicate check and maybe uuid generation
        identifier = re.sub(r'[^a-zA-Z0-9]', '_', name.lower())
        identifier = re.sub(r'_+', '_', identifier)
        identifier = identifier.strip('_')
        return identifier
    except Exception as e:
        raise ValueError(f"Invalid name: {name}")

def delete_processing_stack(session: Session, stack_identifier: str) -> bool:
    """Delete a processing stack and its steps from the database"""
    try:
        # Delete all steps first
        session.query(ProcessingStackStep).filter_by(stack_identifier=stack_identifier).delete()
        
        # Delete the stack
        result = session.query(ProcessingStack).filter_by(identifier=stack_identifier).delete()
        
        session.commit()
        return result > 0
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting processing stack: {e}")
        raise e



#TRANSFORMATIONS_STACKS = {
## See https://docs.llamaindex.ai/en/stable/examples/retrievers/auto_merging_retriever/ for more details on the hierarchical node parser
## List of avaliable transformations stacks with their name and transformations
#    "default": [
#        SentenceSplitter(
#            chunk_size=512,
#            chunk_overlap=64,
#        ),
#    ],
#    #"hierarchical": [ # TODO Fix the bug where a relation with a non existing doc id is created and creates issues when querying the index
#    #    HierarchicalNodeParser.from_defaults(
#    #        include_metadata=True,
#    #        chunk_sizes=[1024, 512, 256, 128], # Stella embedding is trained on 512 tokens chunks so for best performance this is the maximum #size, #we also chunk it into The smallest sentences possible to capture as much atomic meaning of the sentence as possible.
#    #        # When text chunks are too small like under 128 tokens, the embedding model may return null embeddings and we want to avoid that because #it break the search as they can come out on top of the search results
#    #        chunk_overlap=0
#    #    ),
#    #    # Embedding is present at ingestion pipeline level
#    #],
#    "titles": [
#        TitleExtractor(
#            nodes=5,
#        ),
#    ],
#    "questions": [
#        QuestionsAnsweredExtractor(
#            questions=3,
#        ),
#    ],
#    "summary": [
#        SummaryExtractor(
#            summaries=["prev", "self"],
#        ),
#    ],
#    "keywords": [
#        KeywordExtractor(
#            keywords=10,
#        ),
#    ],
#    # NOTE: Current sentence splitter stacks are not linking each node like the hierarchical node parser does, so if multiple are used they are likely #to generate duplicates nodes at retreival time. Only use one at a time to avoid this. # TODO Fix hierarchical node parser
#    "sentence-splitter-2048": [
#        SentenceSplitter(
#            chunk_size=2048,
#            chunk_overlap=256,
#        ),
#    ],
#    "sentence-splitter-1024": [
#        SentenceSplitter(
#            chunk_size=1024,
#            chunk_overlap=128,
#        ),
#    ],
#    "sentence-splitter-512": [
#        SentenceSplitter(
#            chunk_size=512,
#            chunk_overlap=64,
#        ),
#    ],
#    "sentence-splitter-256": [
#        SentenceSplitter(
#            chunk_size=256,
#            chunk_overlap=0,
#        ),
#    ],
#    "sentence-splitter-128": [
#        SentenceSplitter(
#            chunk_size=128,
#            chunk_overlap=0,
#        ),
#    ],
#    "image": [
#        #ImageDescriptionExtractor(
#        #    
#        #),
#        #ImageEXIFExtractor(
#        #    
#        #),
#    ],
#    "video": [
#        #VideoDescriptionExtractor(
#        #    
#        #),
#        #VideoTranscriptionExtractor(
#        #    
#        #),
#        #VideoEXIFExtractor(
#        #    
#        #),
#    ],
#    "audio": [
#        #AudioTranscriptionExtractor(
#        #    
#        #),
#        #AudioEXIFExtractor(
#        #    
#        #),
#    ],
#    "code": [
#        #CodeExtractor(
#        #    
#        #),
#    ],
#    #"entities": [
#    #    EntityExtractor(prediction_threshold=0.5),
#    #],
#    #"zettlekasten": [
#    #    ZettlekastenExtractor(
#    #        similar_notes_top_k=5
#    #    ),
#    #],
#}