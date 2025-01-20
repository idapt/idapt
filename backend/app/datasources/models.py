from pydantic import BaseModel
from typing import Optional

class DatasourceCreate(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    settings: dict = {}
    embedding_provider: str = "ollama_embed"
    embedding_settings: Optional[dict] = None

class DatasourceResponse(BaseModel):
    id: int
    identifier: str
    name: str
    type: str
    description: Optional[str] = None
    settings: dict = {}
    embedding_provider: str
    embedding_settings: Optional[dict] = None

    class Config:
        from_attributes = True

class DatasourceUpdate(BaseModel):
    description: Optional[str] = None
    embedding_provider: Optional[str] = None
    embedding_settings: Optional[dict] = None