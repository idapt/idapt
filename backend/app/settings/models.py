from sqlalchemy import Column, String, JSON
from app.database.models import Base

class Setting(Base):
    __tablename__ = 'settings'
    
    identifier = Column(String, primary_key=True)
    display_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    value = Column(JSON, nullable=False)