from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime, func, JSON, UniqueConstraint, Index
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.declarative import declared_attr
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class Folder(Base):
    __tablename__ = 'folders'
    
    id = Column(Integer, primary_key=True) #The id of the folder
    name = Column(String, nullable=False) #The name of the folder
    parent_id = Column(Integer, ForeignKey('folders.id'), nullable=True) #The parent folder of the folder
    
    children = relationship("Folder", backref='parent', remote_side=[id]) #The children folders of the folder
    files = relationship("File", back_populates="folder") #The files in the folder

class File(Base):
    __tablename__ = 'files'
    
    id = Column(Integer, primary_key=True) #The id of the file
    name = Column(String, nullable=False) #The name of the file
    content = Column(Text, nullable=True) #The content of the file
    file_type = Column(String, nullable=False) #The type of the file
    mime_type = Column(String, nullable=True) #The mime type of the file
    created_at = Column(DateTime, server_default=func.now()) #The date the file was created
    updated_at = Column(DateTime, onupdate=func.now()) #The date the file was last updated
    folder_id = Column(Integer, ForeignKey('folders.id')) #The folder the file belongs to
    
    folder = relationship("Folder", back_populates="files")