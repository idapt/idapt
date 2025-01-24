from sqlalchemy import Column, String, JSON, Boolean, DateTime, Integer, ForeignKey, func, Enum
from sqlalchemy.orm import relationship

from app.database.models import Base

class Datasource(Base):
    __tablename__ = 'datasources'
    
    id = Column(Integer, primary_key=True)
    identifier = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    description = Column(String, nullable=True)
    settings = Column(JSON, nullable=True)
    embedding_provider = Column(String, nullable=False)
    embedding_settings = Column(JSON, nullable=False)  # Store embedding-specific settings
    
    # System tracking
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # The root folder for this datasource
    root_folder_id = Column(Integer, ForeignKey('folders.id'), nullable=True)
    root_folder = relationship("Folder", backref="datasource", uselist=False)