from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime, func, JSON, UniqueConstraint
from sqlalchemy.orm import relationship, declarative_base
from pgvector.sqlalchemy import Vector

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
    embeddings = relationship("DataEmbeddings", back_populates="file")
    nodes = relationship("Node", back_populates="file")

class FileMetadata(Base):
    __tablename__ = 'file_metadata'
    
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey('files.id'))
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)
    
    file = relationship("File", back_populates="file_metadata")

class DataEmbeddings(Base):
    __tablename__ = 'data_embeddings'
    
    id = Column(Integer, primary_key=True)
    text = Column(String, nullable=False)
    metadata_ = Column(JSON)
    node_id = Column(String, ForeignKey('nodes.node_id'))
    doc_id = Column(String, unique=True)
    file_id = Column(Integer, ForeignKey('files.id'))
    embedding = Column(Vector(1024))
    
    file = relationship("File", back_populates="embeddings")
    node = relationship("Node", back_populates="embeddings", primaryjoin="DataEmbeddings.node_id==Node.node_id")

class Node(Base):
    __tablename__ = 'nodes'
    
    id = Column(Integer, primary_key=True)
    node_id = Column(String, unique=True, nullable=False)
    text = Column(Text, nullable=False)
    metadata_ = Column(JSON)
    file_id = Column(Integer, ForeignKey('files.id'))
    created_at = Column(DateTime, server_default=func.now())
    
    file = relationship("File", back_populates="nodes")
    embeddings = relationship("DataEmbeddings", back_populates="node", primaryjoin="Node.node_id==DataEmbeddings.node_id")
