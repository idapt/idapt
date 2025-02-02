import logging
import re
import json
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List
import os

from app.settings.model_initialization import init_embedding_model
from app.settings.schemas import SettingResponse
from app.constants.file_extensions import TEXT_FILE_EXTENSIONS, CODE_FILE_EXTENSIONS
from app.processing_stacks.database.models import ProcessingStack, ProcessingStep, ProcessingStackStep
from app.datasources.database.models import Datasource
from app.datasources.file_manager.schemas import FileInfoResponse
from app.processing_stacks.schemas import (
    ProcessingStackCreate, 
    ProcessingStackResponse, 
    ProcessingStackStepCreate, 
    SentenceSplitterParameters,
    TokenSplitterParameters,
    #CodeSplitterParameters,
    ProcessingStackUpdate, 
    ProcessingStackStepUpdate, 
    ProcessingStackStepResponse, 
    ProcessingStepResponse
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.extractors import (
    TitleExtractor,
    QuestionsAnsweredExtractor,
    SummaryExtractor,
    KeywordExtractor,
)
from llama_index.core.node_parser.text.token import TokenTextSplitter
#from llama_index.core.node_parser.text.code import CodeSplitter
#from app.processing_stacks.utils import get_language_from_extension
logger = logging.getLogger("uvicorn")

def create_default_processing_stacks_if_needed(processing_stacks_db_session: Session):
    """Create default processing stacks in the database"""
    try:
        # Create processing steps
        sentence_splitter_step = processing_stacks_db_session.query(ProcessingStep).filter(ProcessingStep.identifier == "sentence_splitter").first()
        if not sentence_splitter_step:
            step = ProcessingStep(
                type="node_parser",
                identifier="sentence_splitter",
                display_name="Sentence Splitter",
                description="Splits text into sentences with configurable chunk size and overlap",
                parameters_schema=SentenceSplitterParameters.model_json_schema()
            )
            processing_stacks_db_session.add(step)
            processing_stacks_db_session.commit()
            logger.info("Created default processing step 'Sentence Splitter'")

        embedding_step = processing_stacks_db_session.query(ProcessingStep).filter(ProcessingStep.identifier == "embedding").first()
        if not embedding_step:
            step = ProcessingStep(
                type="embedding",
                identifier="embedding",
                display_name="Embedding",
                description="Converts text into vector embeddings for semantic search",
                parameters_schema={}
            )
            processing_stacks_db_session.add(step)
            processing_stacks_db_session.commit()
            logger.info("Created default processing step 'Embedding'")

        token_splitter_step = processing_stacks_db_session.query(ProcessingStep).filter(ProcessingStep.identifier == "token_splitter").first()
        if not token_splitter_step:
            step = ProcessingStep(
                type="node_parser",
                identifier="token_splitter",
                display_name="Token Splitter",
                description="Splits text into chunks based on token count with configurable chunk size and overlap",
                parameters_schema=TokenSplitterParameters.model_json_schema()
            )
            processing_stacks_db_session.add(step)
            processing_stacks_db_session.commit()
            logger.info("Created default processing step 'Token Splitter'")

        #code_splitter_step = session.query(ProcessingStep).filter(ProcessingStep.identifier == "code_splitter").first()
        #if not code_splitter_step:
        #    step = ProcessingStep(
        #        type="node_parser",
        #        identifier="code_splitter",
        #        display_name="Code Splitter",
        #        description="Splits code into chunks using AST parser",
        #        parameters_schema=CodeSplitterParameters.model_json_schema()
        #    )
        #    session.add(step)
        #    session.commit()
        #    logger.info("Created default processing step 'Code Splitter'")

        # Text Processing
        
        # Create the processing stack
        text_processing_stack_create = ProcessingStackCreate(
            display_name="Text Processing",
            description="Processing stack for text data",
            supported_extensions=list(TEXT_FILE_EXTENSIONS),
            steps=[
                ProcessingStackStepCreate(
                    step_identifier="sentence_splitter",
                    order=1,
                    parameters=SentenceSplitterParameters(
                        chunk_size=512,
                        chunk_overlap=128
                    ).model_dump()
                ),
                ProcessingStackStepCreate(
                    step_identifier="embedding",
                    order=2,
                    parameters={}
                )
            ]
        )
        create_processing_stack(processing_stacks_db_session=processing_stacks_db_session, stack=text_processing_stack_create)

        # Create code processing stack
        code_processing_stack_create = ProcessingStackCreate(
            display_name="Code Processing",
            description="Processing stack for code files",
            supported_extensions=list(CODE_FILE_EXTENSIONS),
            steps=[
                ProcessingStackStepCreate(
                    step_identifier="token_splitter",
                    order=1,
                    parameters=TokenSplitterParameters(
                        chunk_size=1024,
                        chunk_overlap=20,
                        separator=" "
                    ).model_dump()
                ),
                #ProcessingStackStepCreate(
                #    step_identifier="code_splitter",
                #    order=1,
                #    parameters=CodeSplitterParameters(
                #        chunk_lines=40,
                #        chunk_lines_overlap=15,
                #        max_chars=1500,
                #        language="python"  # Default language normally not used
                #    ).model_dump()
                #),
                ProcessingStackStepCreate(
                    step_identifier="embedding",
                    order=2,
                    parameters={}
                )
            ]
        )
        create_processing_stack(processing_stacks_db_session=processing_stacks_db_session, stack=code_processing_stack_create)

        # TODO Add image, video, audio, code processing stacks

        processing_stacks_db_session.commit()
    except Exception as e:
        processing_stacks_db_session.rollback()
        logger.error(f"Error creating default processing stacks: {e}")
        raise e    

def create_processing_stack(processing_stacks_db_session: Session, stack: ProcessingStackCreate) -> ProcessingStackResponse:
    """Create a processing stack"""
    try:
        
        # Check for invalid characters in display name
        invalid_chars = '<>:"|?*\\'
        if any(char in stack.display_name for char in invalid_chars):
            raise ValueError(
                f"Processing stack display name contains invalid characters. The following characters are not allowed: {invalid_chars}"
            )

        # Generate identifier
        stack_identifier = generate_stack_identifier(stack.display_name)

        # Try to get the stack from the database
        stack_to_create = processing_stacks_db_session.query(ProcessingStack).filter(ProcessingStack.identifier == stack_identifier).first()
        if stack_to_create:
            #logger.info(f"Processing stack already exists: {stack_to_create.display_name}")
            pass
        else:
            # Create the database stack
            stack_to_create = ProcessingStack(
                identifier=stack_identifier,
                display_name=stack.display_name,
                description=stack.description,
                supported_extensions=json.dumps(stack.supported_extensions),
                steps=[]
            )
            processing_stacks_db_session.add(stack_to_create)
            processing_stacks_db_session.commit()
        
            # Add steps with this function so that validation is done there
            for step in stack.steps:
                add_processing_stack_step(
                    processing_stacks_db_session=processing_stacks_db_session,
                    stack_identifier=stack_identifier,
                    step_identifier=step.step_identifier,
                    order=step.order,
                    parameters=step.parameters or {}
                )

        response = ProcessingStackResponse(
            identifier=stack_to_create.identifier,
            display_name=stack_to_create.display_name,
            supported_extensions=json.loads(stack_to_create.supported_extensions),
            description=stack_to_create.description,
            is_enabled=stack_to_create.is_enabled,
            steps=[ ProcessingStackStepResponse(
                id=step.id,
                order=step.order,
                parameters=step.parameters,
                step_identifier=step.step_identifier,
                step=ProcessingStepResponse(
                    identifier=step.step.identifier,
                    display_name=step.step.display_name,
                    description=step.step.description,
                    type=step.step.type,
                    parameters_schema=step.step.parameters_schema
                )
            ) for step in sorted(stack_to_create.steps, key=lambda x: x.order) ]
        )
    
        return response
    
    except Exception as e:
        processing_stacks_db_session.rollback()
        logger.error(f"Error creating processing stack: {e}")
        raise e
    
def update_processing_stack(processing_stacks_db_session: Session, stack_identifier: str, stack_update: ProcessingStackUpdate) -> ProcessingStackResponse:
    """Update a processing stack"""
    try:

        db_stack = processing_stacks_db_session.query(ProcessingStack).filter_by(identifier=stack_identifier).first()
        if not db_stack:
            raise HTTPException(status_code=404, detail="Stack not found")
        
        # Validate steps
        if stack_update.steps:
            # Try to get the steps from the database
            parser_count = 0
            embedding_count = 0
            for stack_step in stack_update.steps:
                db_step = processing_stacks_db_session.query(ProcessingStep).filter_by(identifier=stack_step.step_identifier).first()
                # If the step is not found, raise an error
                if not db_step:
                    raise ValueError(f"Step not found: {stack_step.step_identifier}")
                
                # Make sure the first stack step is of type node parser or embedding
                if stack_step.order == 1 and db_step.type not in ["node_parser", "embedding"]:
                    raise ValueError(f"First step must be a node parser or embedding")
                
                # Make sure the last stack step is of type embedding
                if stack_step.order == len(stack_update.steps) and db_step.type != "embedding":
                    raise ValueError(f"Last step must be an embedding")
                
                # Count node parsers and embeddings
                if db_step.type == "node_parser":
                    parser_count += 1
                elif db_step.type == "embedding":
                    embedding_count += 1
            
            # Check if the counts are correct
            if parser_count != 1:
                raise ValueError("Exactly one node parser is required")
            if embedding_count != 1:
                raise ValueError("Exactly one embedding step is required")
            
        # Update supported extensions
        db_stack.supported_extensions = json.dumps(stack_update.supported_extensions)
        
        # Delete existing steps
        processing_stacks_db_session.query(ProcessingStackStep).filter_by(stack_identifier=stack_identifier).delete()
        
        # Add new steps
        for stack_step in stack_update.steps:
            add_processing_stack_step(
                processing_stacks_db_session=processing_stacks_db_session,
                stack_identifier=stack_identifier,
                step_identifier=stack_step.step_identifier,
                order=stack_step.order,
                parameters=stack_step.parameters or {}
            )
        
        processing_stacks_db_session.commit()
        
        # Return updated stack
        updated_stack = processing_stacks_db_session.query(ProcessingStack).filter_by(identifier=stack_identifier).first()
        return ProcessingStackResponse(
            identifier=updated_stack.identifier,
            display_name=updated_stack.display_name,
            supported_extensions=json.loads(updated_stack.supported_extensions),
            description=updated_stack.description,
            is_enabled=updated_stack.is_enabled,
            steps=[
                ProcessingStackStepResponse(
                    id=step.id,
                    order=step.order,
                    parameters=step.parameters,
                    step_identifier=step.step_identifier,
                    step=ProcessingStepResponse(
                        identifier=step.step.identifier,
                        display_name=step.step.display_name,
                        description=step.step.description,
                        type=step.step.type,
                        parameters_schema=step.step.parameters_schema
                    )
                )
                for step in sorted(updated_stack.steps, key=lambda x: x.order)
            ]
        )

    except Exception as e:
        processing_stacks_db_session.rollback()
        logger.error(f"Error updating processing stack: {e}")
        raise e
    
def get_processing_stacks(processing_stacks_db_session: Session) -> List[ProcessingStackResponse]:
    """Get all processing stacks"""
    try:
        stacks = processing_stacks_db_session.query(ProcessingStack).all()
        return [get_processing_stack(processing_stacks_db_session=processing_stacks_db_session, stack_identifier=stack.identifier) for stack in stacks]
    except Exception as e:
        logger.error(f"Error getting processing stacks: {e}")
        raise e
    
def get_processing_stack(processing_stacks_db_session: Session, stack_identifier: str) -> ProcessingStackResponse:
    """Get a processing stack"""
    try:
        stack = processing_stacks_db_session.query(ProcessingStack).filter_by(identifier=stack_identifier).first()
        return ProcessingStackResponse(
            identifier=stack.identifier,
            display_name=stack.display_name,
            description=stack.description,
            supported_extensions=json.loads(stack.supported_extensions),
            is_enabled=stack.is_enabled,
            steps=[
                ProcessingStackStepResponse(
                    id=stack_step.id,
                    step_identifier=stack_step.step_identifier,
                    order=stack_step.order,
                    parameters=stack_step.parameters,
                    step=ProcessingStepResponse(
                        identifier=stack_step.step.identifier,
                        display_name=stack_step.step.display_name,
                        description=stack_step.step.description,
                        type=stack_step.step.type,
                        parameters_schema=stack_step.step.parameters_schema
                    )
                ) for stack_step in sorted(stack.steps, key=lambda x: x.order)
            ]
        )
    except Exception as e:
        logger.error(f"Error getting processing stack: {e}")
        raise e

def get_default_parameters(parameters_schema: dict) -> dict:
    """Extract default values from a parameters schema"""
    default_params = {}
    if 'properties' in parameters_schema:
        for prop_name, prop_schema in parameters_schema['properties'].items():
            if 'default' in prop_schema:
                default_params[prop_name] = prop_schema['default']
    return default_params

def add_processing_stack_step(processing_stacks_db_session: Session, stack_identifier: str, step_identifier: str, order: int, parameters: dict | None = None):
    """Add a processing stack step to a processing stack in the database"""
    try:
        # Get the step to access its schema
        step = processing_stacks_db_session.query(ProcessingStep).filter_by(identifier=step_identifier).first()
        if not step:
            raise ValueError(f"Step not found: {step_identifier}")

        # Get default parameters from schema
        default_params = get_default_parameters(step.parameters_schema)
        
        # Merge provided parameters with defaults
        final_parameters = {**default_params, **(parameters or {})}

        processing_stacks_db_session.add(ProcessingStackStep(
            stack_identifier=stack_identifier, 
            step_identifier=step_identifier, 
            order=order, 
            parameters=final_parameters
        ))
        processing_stacks_db_session.commit()
    except Exception as e:
        processing_stacks_db_session.rollback()
        logger.error(f"Error adding processing stack step: {e}")
        raise e
    
def delete_processing_stack_step(processing_stacks_db_session: Session, stack_identifier: str, step_identifier: str):
    """Delete a processing stack step from the database"""
    try:
        processing_stacks_db_session.query(ProcessingStackStep).filter_by(stack_identifier=stack_identifier, step_identifier=step_identifier).delete()
        processing_stacks_db_session.commit()
    except Exception as e:
        processing_stacks_db_session.rollback()
        logger.error(f"Error deleting processing stack step: {e}")
        raise e

def change_processing_stack_step_order(processing_stacks_db_session: Session, stack_identifier: str, step_identifier: str, new_order: int):
    """Change the order of a processing stack step in the database"""
    try:
        # Get the step to move and its current order
        step_to_move = processing_stacks_db_session.query(ProcessingStackStep).filter_by(
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
        other_steps = processing_stacks_db_session.query(ProcessingStackStep).filter_by(
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
        
        processing_stacks_db_session.commit()
    except Exception as e:
        processing_stacks_db_session.rollback()
        logger.error(f"Error changing processing stack step order: {e}")
        raise e

def get_transformer_for_step(step: ProcessingStep, parameters: dict, datasource: Datasource, file_response: FileInfoResponse, embedding_settings_response: SettingResponse):
    """Convert a ProcessingStep and parameters into a LlamaIndex transformer"""
    try:
        match step.identifier:
            case "sentence_splitter":
                return SentenceSplitter(**parameters)
            #case "code_splitter":
            #    # Get file extension from file response
            #    file_extension = os.path.splitext(file_response.path)[1].lower()
            #    
            #    # Try to detect language from extension
            #    detected_language = get_language_from_extension(file_extension)
            #    
            #    if detected_language:
            #        logger.debug(f"Detected language '{detected_language}' for file extension '{file_extension}'")
            #        # Create CodeSplitter with detected language and parameters
            #        #return CodeSplitter.from_defaults(
            #        #    language=detected_language,
            #        #    chunk_lines=parameters.get("chunk_lines", 40),
            #        #    chunk_lines_overlap=parameters.get("chunk_lines_overlap", 15),
            #        #    max_chars=parameters.get("max_chars", 1500)
            #        #)
            #        # TODO: Code splitter always cause init error, so we use a normal text splitter for now

            #    else:
            #        logger.warning(f"No language detected for extension '{file_extension}' for file '{file_response.original_path}', falling back to sentence splitter")
            #        # Fall back to sentence splitter for unknown extensions
            #        return TokenTextSplitter(
            #            include_metadata=True,
            #            include_prev_next_rel=True,
            #            chunk_size=parameters.get("chunk_size", 512),
            #            chunk_overlap=parameters.get("chunk_overlap", 128)
            #        )
            case "token_splitter":
                return TokenTextSplitter(
                    chunk_size=parameters.get("chunk_size", 1024),
                    chunk_overlap=parameters.get("chunk_overlap", 20),
                    separator=parameters.get("separator", " "),
                    include_metadata=True,
                    include_prev_next_rel=True
                )
            case "embedding":
                return init_embedding_model(embedding_settings_response.schema_identifier, embedding_settings_response.value_json)
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

def get_transformations_for_stack(processing_stacks_db_session: Session, stack_identifier: str, datasource: Datasource, file_response: FileInfoResponse, embedding_settings_response: SettingResponse):
    """Get all transformations for a processing stack"""
    try:
        stack = processing_stacks_db_session.query(ProcessingStack).filter_by(identifier=stack_identifier).first()
        if not stack:
            raise ValueError(f"Stack not found: {stack_identifier}")
          
        transformations = []
        stack_steps = (processing_stacks_db_session.query(ProcessingStackStep)
                      .filter_by(stack_identifier=stack_identifier)
                      .order_by(ProcessingStackStep.order)
                      .all())
                      
        for stack_step in stack_steps:
            transformer = get_transformer_for_step(stack_step.step, stack_step.parameters or {}, datasource, file_response, embedding_settings_response)
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

def delete_processing_stack(processing_stacks_db_session: Session, stack_identifier: str) -> bool:
    """Delete a processing stack and its steps from the database"""
    try:
        # Delete all steps first
        processing_stacks_db_session.query(ProcessingStackStep).filter_by(stack_identifier=stack_identifier).delete()
        
        # Delete the stack
        result = processing_stacks_db_session.query(ProcessingStack).filter_by(identifier=stack_identifier).delete()
        
        processing_stacks_db_session.commit()
        return result > 0
    except Exception as e:
        processing_stacks_db_session.rollback()
        logger.error(f"Error deleting processing stack: {e}")
        raise e

def validate_processing_stack_steps(processing_stacks_db_session: Session, steps: List[ProcessingStackStepCreate]) -> None:
    if not steps:
        raise ValueError("At least one step is required")
        
    # Get all steps from database to check their types
    step_types = {
        step.identifier: step.type 
        for step in processing_stacks_db_session.query(ProcessingStep).filter(
            ProcessingStep.identifier.in_([s.step_identifier for s in steps])
        ).all()
    }
    
    # Validate first step is node parser
    if step_types.get(steps[0].step_identifier) != "node_parser":
        raise ValueError("First step must be a node parser")
        
    # Validate last step is embedding
    if step_types.get(steps[-1].step_identifier) != "embedding":
        raise ValueError("Last step must be an embedding")
        
    # Count node parsers and embeddings
    parser_count = sum(1 for s in steps if step_types.get(s.step_identifier) == "node_parser")
    embedding_count = sum(1 for s in steps if step_types.get(s.step_identifier) == "embedding")
    
    if parser_count != 1:
        raise ValueError("Exactly one node parser is required")
    if embedding_count != 1:
        raise ValueError("Exactly one embedding step is required")

def get_language_from_extension(file_extension: str) -> str | None:
    """Map file extension to tree-sitter language name"""
    extension_to_language = {
        # Web Technologies
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".html": "html",
        ".css": "css",
        
        # Systems Programming
        ".c": "c",
        ".h": "c",
        ".cpp": "cpp",
        ".hpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".rs": "rust",
        ".go": "go",
        
        # JVM Languages
        ".java": "java",
        ".scala": "scala",
        ".kt": "kotlin",
        
        # .NET Languages
        ".cs": "c_sharp",
        
        # Scripting Languages
        ".py": "python",
        ".rb": "ruby",
        ".php": "php",
        ".pl": "perl",
        ".sh": "bash",
        ".bash": "bash",
        ".lua": "lua",
        ".r": "r",
        ".jl": "julia",
        
        # Query Languages
        ".sql": "sql",
        ".sqlite": "sql",
        ".graphql": "ql",
        ".gql": "ql",
        
        # Configuration & Data
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".hcl": "hcl",
        ".dockerfile": "dockerfile",
        ".mod": "go_mod",
        
        # Functional Languages
        ".hs": "haskell",
        ".ml": "ocaml",
        ".mli": "ocaml",
        ".ex": "elixir",
        ".exs": "elixir",
        ".elm": "elm",
        ".cl": "commonlisp",
        ".lisp": "commonlisp",
        ".el": "elisp",
        
        # Scientific Computing
        ".f90": "fortran",
        ".f95": "fortran",
        ".f03": "fortran",
        ".f08": "fortran",
        ".f": "fixed_form_fortran",
        ".for": "fixed_form_fortran",
        ".f77": "fixed_form_fortran",
        
        # Mobile Development
        ".swift": "swift",
        ".m": "objc",
        ".mm": "objc",
        
        # Other
        ".erl": "erlang",
        ".hack": "hack",
        ".dot": "dot",
        ".makefile": "make",
        ".mk": "make",
    }
    return extension_to_language.get(file_extension.lower())