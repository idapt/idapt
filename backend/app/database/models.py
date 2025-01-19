from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, func, JSON, Enum
from sqlalchemy.orm import relationship, declarative_base
import enum

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
    
    # Processing status
    status = Column(Enum(FileStatus), default=FileStatus.PENDING, nullable=False)
    
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

class ProcessingStep(Base):
    __tablename__ = 'processing_steps'
    
    identifier = Column(String, primary_key=True)
    display_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    type = Column(String, nullable=False)  # 'node_parser', 'extractor', 'embedding'
    parameters_schema = Column(JSON, nullable=False)  # JSON schema defining available parameters
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class ProcessingStack(Base):
    __tablename__ = 'processing_stacks'
    
    identifier = Column(String, primary_key=True)
    display_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    is_enabled = Column(Boolean, default=True)
    supported_extensions = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class ProcessingStackStep(Base):
    __tablename__ = 'processing_stack_steps'
    
    id = Column(Integer, primary_key=True)
    stack_identifier = Column(String, ForeignKey('processing_stacks.identifier', ondelete='CASCADE'))
    step_identifier = Column(String, ForeignKey('processing_steps.identifier', ondelete='CASCADE'))
    order = Column(Integer, nullable=False)
    parameters = Column(JSON, nullable=True)  # Actual parameters for this step in this stack
    
    stack = relationship("ProcessingStack", backref="steps")
    step = relationship("ProcessingStep", backref="stack_steps")

class Setting(Base):
    __tablename__ = 'settings'
    
    identifier = Column(String, primary_key=True)
    display_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    value = Column(JSON, nullable=False)