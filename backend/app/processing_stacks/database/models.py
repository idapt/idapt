from sqlalchemy import Column, String, JSON, Boolean, DateTime, Integer, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ProcessingStep(Base):
    __tablename__ = 'processing_steps'
    
    identifier = Column(String, primary_key=True)
    display_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    type = Column(String, nullable=False)  # 'node_parser', 'node_post_processor', 'embedding'
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
