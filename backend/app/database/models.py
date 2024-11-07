from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime, func, JSON, UniqueConstraint, Index
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.declarative import declared_attr
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class Folder(Base):
    __tablename__ = 'folders'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey('folders.id'), nullable=True)
    
    # Original metadata
    original_created_at = Column(DateTime, nullable=True)
    original_modified_at = Column(DateTime, nullable=True)
    
    # System tracking
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    children = relationship("Folder", backref='parent', remote_side=[id])
    files = relationship("File", back_populates="folder")

class File(Base):
    __tablename__ = 'files'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)
    
    # Original metadata
    original_created_at = Column(DateTime, nullable=True)
    original_modified_at = Column(DateTime, nullable=True)
    
    # System tracking
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    folder_id = Column(Integer, ForeignKey('folders.id'))
    folder = relationship("Folder", back_populates="files")
    data = relationship("DataFile", back_populates="file")

# Table containing the processed / extracted data from the files
class Data(Base):
    __tablename__ = 'data'
    
    id = Column(Integer, primary_key=True)
    data = Column(JSON, nullable=False)
    files = relationship("DataFile", back_populates="data")

# Table linking data to files
class DataFile(Base):
    __tablename__ = 'data_files'
    
    id = Column(Integer, primary_key=True)
    data_id = Column(Integer, ForeignKey('data.id'))
    file_id = Column(Integer, ForeignKey('files.id'))
    data = relationship("Data", back_populates="files")
    file = relationship("File", back_populates="data_files")