from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime, func
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Folder(Base):
    __tablename__ = 'folders'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey('folders.id'), nullable=True)
    
    children = relationship("Folder", backref='parent', remote_side=[id])
    files = relationship("File", back_populates="folder")

class File(Base):
    __tablename__ = 'files'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    folder_id = Column(Integer, ForeignKey('folders.id'))
    
    folder = relationship("Folder", back_populates="files")
    file_metadata = relationship("FileMetadata", back_populates="file", uselist=False)

class FileMetadata(Base):
    __tablename__ = 'file_metadata'
    
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey('files.id'))
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)
    
    file = relationship("File", back_populates="file_metadata")