from typing import List
from pydantic import BaseModel, Field
from llama_index.core.schema import Document
from app.engine.pipelines.base import BaseData

import logging
logger = logging.getLogger(__name__)

note_json_schema = """{
    "zettlekasten_atomic_note_title": "",
    "zettlekasten_atomic_note_markdown_content_strictly_about_title": "",
    "questions_this_note_answers": ["..."],
    "tags_keywords_this_note_is_about": ["..."]
}"""

class ZettlekastenNote(BaseModel):
    """Model for a Zettlekasten note"""
    zettlekasten_atomic_note_title: str = Field(..., description="Title of the note")
    zettlekasten_atomic_note_markdown_content_strictly_about_title: str = Field(..., description="Main content of the note")
    questions_this_note_answers: List[str] = Field(..., description="Questions that this note helps answer")
    tags_keywords_this_note_is_about: List[str] = Field(..., description="Tags or keywords that this note is about")
    # Dont but the source file ids here as it will be filled by the llm and managed externally

    @classmethod
    def to_base_data(cls, zettlekasten_note: 'ZettlekastenNote', source_file_ids: List[int]) -> BaseData:
        """Convert a single note to a BaseData object"""
        try:
            return BaseData(
                # Just convert the note to a json string and put it in the content field
                source_file_ids=source_file_ids,
                content=zettlekasten_note.model_dump_json()
            )
        except Exception as e:
            logger.error(f"Error converting ZettlekastenNote to BaseData: {e}")
            return None

from typing import Dict, Any, List
from llama_index.core import Settings
import json
import re

from app.engine.pipelines.base import GenerateDataPipeline
from llama_index.core.settings import Settings
from app.engine.index import get_index

class ZettlekastenPipeline(GenerateDataPipeline):
    def __init__(self):
        self.similarity_threshold = 0.85
        self.index = get_index()

    async def extract_titles(self, content: str) -> List[str]:
        try:
            prompt = (
                "Extract a list of potential Titles for Zettlekasten Atomic Notes from the following Journaling Entry. "
                "The output should be a JSON object with a \"titles\" array containing strings.\n\n"
                f"Journaling Entry:\n{content}\n\n"
                "Expected JSON format:\n{\"titles\": [\"Title 1\", \"Title 2\", ...]}\n\n"
                "Generated JSON:"
            )
            num_attempts = 0
            while num_attempts < 10:
                num_attempts += 1
                
                logger.info("Generating titles with LLM")
                response = await Settings.llm.acomplete(prompt)
                response_text = response.text.strip()

                try:
                    # Find the first { and last } in the response
                    start_index = response_text.find('{')
                    end_index = response_text.rfind('}') + 1
                    
                    if start_index == -1 or end_index == 0:
                        logger.error("No JSON object found in response")
                        continue
                        
                    # Extract just the JSON part and clean it
                    json_str = response_text[start_index:end_index]
                    # Clean the JSON string
                    json_str = (json_str
                        .replace('\n', ' ')  # Replace newlines with spaces as this is title generation
                        .replace('```', '')  # Remove any code blocks
                    )
                    
                    logger.info(f"LLM generated titles response: {response_text}")

                    # Parse the JSON and extract titles
                    data = json.loads(json_str)
                    if isinstance(data, dict) and 'titles' in data:
                        return data['titles']
                    else:
                        logger.error("Response missing 'titles' key")
                        continue

                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON in the titles response, retrying: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error extracting titles: {e}")
            return []

    async def update_or_create_note(
        self, title: str, content: str, similar_note: str = None
    ) -> ZettlekastenNote:
        try:
            if similar_note:
                prompt = (
                    f"Rewrite the following Zettlekasten Existing Atomic Note strictly on the subject of the Title, gather all new relevant information on the subject from the New Content.\n\n"
                    f"Title:\n{title}\n\n"
                    f"Zettlekasten Existing Atomic Note:\n{similar_note}\n\n"
                    f"New Content:\n{content}\n\n"
                    f"JSON Schema to fill:\n{note_json_schema}\n\n"
                    f"Filled JSON Schema:\n"
                )
            else:
                prompt = (
                    f"Fill the JSON Schema by creating a Zettlekasten Atomic Note strictly on the subject of the Title, gather all relevant information on the subject from the Content.\n\n"
                    f"Title:\n{title}\n\n"
                    f"Content:\n{content}\n\n"
                    f"JSON Schema to fill:\n{note_json_schema}\n\n"
                    f"Filled JSON Schema:\n"
                )
            #logger.info(f"Prompt: {prompt}")

            num_attempts = 0
            while num_attempts < 10:
                num_attempts += 1
                
                logger.info(f"Generating note for title: {title} with LLM, attempt {num_attempts}")

                response = await Settings.llm.acomplete(prompt)
                response_text = response.text.strip()
                                
                try:
                    # Find the first { and last } in the response
                    start_index = response_text.find('{')
                    end_index = response_text.rfind('}') + 1
                    
                    if start_index == -1 or end_index == 0:
                        logger.error("No JSON object found in response")
                        return None

                    # Extract just the JSON part
                    json_str = response_text[start_index:end_index]

                    logger.info(f"LLM generated note JSON: {json_str}")
                    
                    # Parse the JSON
                    note_data = json.loads(json_str, strict=False)
                    
                    # Create the note from the json data
                    note = ZettlekastenNote(
                        zettlekasten_atomic_note_title=str(note_data["zettlekasten_atomic_note_title"]).strip(),
                        zettlekasten_atomic_note_markdown_content_strictly_about_title=str(note_data["zettlekasten_atomic_note_markdown_content_strictly_about_title"]).strip(),
                        questions_this_note_answers=[str(q).strip() for q in note_data["questions_this_note_answers"]],
                        tags_keywords_this_note_is_about=[str(t).strip() for t in note_data["tags_keywords_this_note_is_about"]]
                    )
                    return note
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON from LLM response: {e}\nJSON string: {json_str}\n Retrying...")
                    
        except Exception as e:
            logger.error(f"Error in update_or_create_note: {e}")
            return None

    async def generate(self, source_file_ids: List[int], content: str) -> List[BaseData]:
        try:
            titles = await self.extract_titles(content)
            base_data_list = []

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
                note = await self.update_or_create_note(title, content)
                
                if note:                
                    # Convert the note to a BaseData object 
                    base_data = ZettlekastenNote.to_base_data(note, source_file_ids)
                    # Add the base data to the list of data to return
                    base_data_list.append(base_data)

            # Return the list of base data
            return base_data_list

        except Exception as e:
            logger.error(f"Error in ZettlekastenPipeline generate: {e}")
            return []