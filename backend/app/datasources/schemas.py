from pydantic import BaseModel
from typing import Optional, Literal
from app.datasources.database.models import DatasourceType

class DatasourceCreate(BaseModel):
    name: str
    type: Literal[DatasourceType.FILES.name, DatasourceType.CHATS.name, DatasourceType.WINDOWS_SYNC.name]
    description: Optional[str] = None
    settings_json: str = "{}"
    embedding_setting_identifier: str = None

class DatasourceResponse(BaseModel):
    identifier: str
    name: str
    type: Literal[DatasourceType.FILES.name, DatasourceType.CHATS.name, DatasourceType.WINDOWS_SYNC.name]
    description: Optional[str] = None
    settings_json: str = "{}"
    embedding_setting_identifier: str

class DatasourceUpdate(BaseModel):
    description: Optional[str] = None
    embedding_setting_identifier: Optional[str] = None