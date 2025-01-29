from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean, Text, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Chat(Base):
    __tablename__ = 'chat'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    last_opened_at = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    messages = relationship("Message", back_populates="chat")

class Message(Base):
    __tablename__ = 'message'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, ForeignKey('chat.id'), nullable=False)
    role = Column(String, nullable=False)
    #previousMessageId = Column(Integer, ForeignKey('message.id'), nullable=True)
    content = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    is_upvoted = Column(Boolean, nullable=True) # NULL if not upvoted, False if downvoted, True if upvoted
    
    # Relationships
    chat = relationship("Chat", back_populates="messages")

#class Document(Base):
#    __tablename__ = 'Document'
#    
#    id = Column(UUID, primary_key=True, default=uuid4)
#    createdAt = Column(DateTime, primary_key=True)
#    title = Column(Text, nullable=False)
#    content = Column(Text)
#    text = Column(String, nullable=False, default='text')
#    
#    # Relationships
#    suggestions = relationship("Suggestion", back_populates="document")
#
#class Suggestion(Base):
#    __tablename__ = 'Suggestion'
#    
#    id = Column(UUID, primary_key=True, default=uuid4)
#    documentId = Column(UUID, nullable=False)
#    documentCreatedAt = Column(DateTime, nullable=False)
#    originalText = Column(Text, nullable=False)
#    suggestedText = Column(Text, nullable=False)
#    description = Column(Text)
#    isResolved = Column(Boolean, default=False, nullable=False)
#    createdAt = Column(DateTime, nullable=False)
#    
#    # Relationships
#    document = relationship("Document", 
#                          foreign_keys=[documentId, documentCreatedAt],
#                          primaryjoin="and_(Suggestion.documentId == Document.id, "
#                                    "Suggestion.documentCreatedAt == Document.createdAt)",
#                          back_populates="suggestions")
