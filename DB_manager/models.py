#DB에 저장할 TABLE 형태 확정

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from database import Base

class Word(Base):
    __tablename__ = 'words'
    id = Column(Integer, primary_key = True, index = True)
    gallId = Column(String(50))
    date = Column(DateTime(timezone= True))
    wordContent = Column(String(150))
    sentiment = Column(Float)