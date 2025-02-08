from sqlalchemy import Column, String, JSON, Boolean, DateTime, Integer, ForeignKey, func, Enum
from sqlalchemy.orm import relationship
import enum
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Folder(Base):
    __tablename__ = 'folders'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False, unique=True)
    original_path = Column(String, nullable=False, unique=True)
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
    original_path = Column(String, nullable=False, unique=True)
    mime_type = Column(String, nullable=True)
    size = Column(Integer, nullable=True)
    dek = Column(String, nullable=False)
    
    # Processing status
    status = Column(Enum(FileStatus), default=FileStatus.PENDING, nullable=False)
    error_message = Column(String, nullable=True)
    
    # Processing stacks tracking
    processed_stacks = Column(JSON, nullable=True)  # List of already processed stacks
    stacks_to_process = Column(JSON, nullable=True)  # List of stacks queued for processing
    processing_started_at = Column(DateTime, nullable=True)
    
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

