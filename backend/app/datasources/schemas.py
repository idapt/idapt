import json
from pydantic import BaseModel
from typing import Optional
from app.datasources.models import Datasource

class DatasourceCreate(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    settings: dict = {}
    embedding_provider: str
    embedding_settings_json: Optional[str] = "{}"

class DatasourceResponse(BaseModel):
    id: int
    identifier: str
    name: str
    type: str
    description: Optional[str] = None
    settings: dict = {}
    embedding_provider: str
    embedding_settings: Optional[str] = "{}"

    @staticmethod
    def from_model(model: Datasource):
        from app.settings.schemas import get_embedding_provider_class

        # Match the embedding provider to the class
        embedding_provider_class = get_embedding_provider_class(model.embedding_provider)
        embedding_settings = embedding_provider_class.model_validate_json(model.embedding_settings)
            
        return DatasourceResponse(
            id=model.id,
            identifier=model.identifier,
            name=model.name,
            type=model.type,
            description=model.description,
            settings={},#model.settings,
            embedding_provider=model.embedding_provider,
            embedding_settings=embedding_settings.model_dump_json()
        )

class DatasourceUpdate(BaseModel):
    description: Optional[str] = None
    embedding_provider: Optional[str] = None
    embedding_settings_json: Optional[str] = None