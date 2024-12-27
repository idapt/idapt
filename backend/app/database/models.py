from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, func, JSON, Enum
from sqlalchemy.orm import relationship, declarative_base
import enum

Base = declarative_base()

class Folder(Base):
    __tablename__ = 'folders'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False, unique=True)
    parent_id = Column(Integer, ForeignKey('folders.id'), nullable=True)
    
    # System tracking
    uploaded_at = Column(DateTime, server_default=func.now())
    accessed_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    children = relationship("Folder", backref='parent', remote_side=[id])
    files = relationship("File", back_populates="folder")

class FileStatus(enum.Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"

class File(Base):
    __tablename__ = 'files'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False, unique=True)
    mime_type = Column(String, nullable=True)
    size = Column(Integer, nullable=True)
    
    # Processing status
    status = Column(Enum(FileStatus), default=FileStatus.PENDING, nullable=False)
    
    # Processing stacks tracking
    processed_stacks = Column(JSON, nullable=True)  # List of already processed stacks
    stacks_to_process = Column(JSON, nullable=True)  # List of stacks queued for processing
    
    # Original metadata
    file_created_at = Column(DateTime, nullable=False)
    file_modified_at = Column(DateTime, nullable=False)
    
    # System tracking
    uploaded_at = Column(DateTime, server_default=func.now())
    accessed_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # LlamaIndex document references
    ref_doc_ids = Column(JSON, nullable=True)
    
    # Relationships
    folder_id = Column(Integer, ForeignKey('folders.id'))
    folder = relationship("Folder", back_populates="files")

class Datasource(Base):
    __tablename__ = 'datasources'
    
    id = Column(Integer, primary_key=True)
    identifier = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    description = Column(String, nullable=True)
    settings = Column(JSON, nullable=True)
    
    # System tracking
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # The root folder for this datasource
    root_folder_id = Column(Integer, ForeignKey('folders.id'), nullable=True)
    root_folder = relationship("Folder", backref="datasource", uselist=False)
