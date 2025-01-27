from sqlalchemy import Column, String, JSON
from app.database.models import Base

class Setting(Base):
    __tablename__ = 'settings'
    
    identifier = Column(String, primary_key=True)
    schema_identifier = Column(String, nullable=False)  # e.g. "ollama_embed", "openai_llm", "app"
    setting_schema_json = Column(JSON, nullable=False)  # Stores the Pydantic model's JSON schema
    value_json = Column(JSON, nullable=False)
