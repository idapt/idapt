from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, func, JSON
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Folder(Base):
    __tablename__ = 'folders'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey('folders.id'), nullable=True)
    
    # System tracking
    uploaded_at = Column(DateTime, server_default=func.now())
    accessed_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    children = relationship("Folder", backref='parent', remote_side=[id])
    files = relationship("File", back_populates="folder")

class File(Base):
    __tablename__ = 'files'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)
    size = Column(Integer, nullable=True)
    
    # Original metadata
    file_created_at = Column(DateTime, nullable=False)
    file_modified_at = Column(DateTime, nullable=False)
    
    # System tracking
    uploaded_at = Column(DateTime, server_default=func.now())
    accessed_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    folder_id = Column(Integer, ForeignKey('folders.id'))
    folder = relationship("Folder", back_populates="files")

class Datasource(Base):
    __tablename__ = 'datasources'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    type = Column(String, nullable=False)  # e.g., 'files', 'database', 'api'
    settings = Column(JSON, nullable=True)  # Store datasource-specific settings
    
    # System tracking
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # The root folder for this datasource
    root_folder_id = Column(Integer, ForeignKey('folders.id'), nullable=False)
    root_folder = relationship("Folder", backref="datasource", uselist=False)