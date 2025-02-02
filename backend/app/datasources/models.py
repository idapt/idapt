from sqlalchemy import Column, String, JSON, DateTime, Integer, ForeignKey, func
from sqlalchemy.orm import relationship
import enum
from app.database.models import Base

class DatasourceType(enum.Enum):
    FILES = "files"
    WINDOWS_SYNC = "windows_sync"
    CHATS = "chats"

class Datasource(Base):
    __tablename__ = 'datasources'
    
    identifier = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    description = Column(String, nullable=True)
    settings_json = Column(JSON, nullable=True)
    
    # System tracking
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # The root folder for this datasource
    folder_id = Column(Integer, ForeignKey('folders.id'), nullable=True)
    folder = relationship("Folder", backref="datasource", uselist=False)
    
    # Relationship to embedding settings
    embedding_setting_identifier = Column(String, ForeignKey('settings.identifier'), nullable=False)
    embedding_setting = relationship("Setting", backref="datasource")