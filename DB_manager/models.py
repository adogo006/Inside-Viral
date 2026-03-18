#DB에 저장할 TABLE 형태 확정

from sqlalchemy import Column, Integer, String, Float, DateTime, TEXT
from sqlalchemy.sql import func
from DB_manager.database import Base
from enum import Enum

class ProcessState(str, Enum):
    PENDING = "pending"         # 크롤링 직후
    COMPLETED = "completed"   # NLP 직후

class Word(Base):
    __tablename__ = 'words'
    id = Column(Integer, primary_key = True, index = True)
    gallId = Column(String(50))
    date = Column(DateTime(timezone= True))
    wordContent = Column(TEXT)
    sentiment = Column(Float)
    state = Column(String(20), default = ProcessState.PENDING) # pending 기본값, nlp 처리 후 completed 로 변경