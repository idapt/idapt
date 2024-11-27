from pydantic import BaseModel, Field
from typing import List

class ZettlekastenNoteTitleList(BaseModel):
    """Model for a list of Zettlekasten note titles"""
    titles: List[str] = Field(..., description="List of Zettlekasten note titles")

class ZettlekastenNote(BaseModel):
    """Model for a Zettlekasten note"""
    zettlekasten_atomic_note_title: str = Field(..., description="Title of the note")
    zettlekasten_atomic_note_markdown_content_strictly_about_title: str = Field(..., description="Main content of the note")
    questions_this_note_answers: List[str] = Field(..., description="Questions that this note helps answer")
    tags_keywords_this_note_is_about: List[str] = Field(..., description="Tags or keywords that this note is about")
