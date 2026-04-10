#DB에 저장할 TABLE 형태 확정

from sqlalchemy import Column, Integer, String, Float, DateTime, TEXT, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.sql import func
from database import Base
from enum import Enum

class ProcessState(str, Enum):
    PENDING = "pending"         # 크롤링 직후
    COMPLETED = "completed"   # sentiment 할당 직후

class LearningState(str, Enum):
    PENDING = "pending"         # 크롤링 직후
    COMPLETED = "completed"   # sentiment 할당 직후

class RequestStatus(str, Enum):
    """크롤링 요청의 생명주기 상태"""
    PENDING = "pending"              # 초기 상태
    RUNNING = "running"              # 크롤러에서 실행 중
    SUCCEEDED = "succeeded"          # 크롤링 성공
    FAILED = "failed"                # 크롤링 실패
    CANCELLED = "cancelled"          # 사용자가 취소
    CANCELLING = "cancelling"        # 취소 중
    DISPATCH_FAILED = "dispatch_failed"  # 크롤러로의 요청 실패

class Word(Base):
    __tablename__ = 'words'
    id = Column(Integer, primary_key = True, index = True)
    gallId = Column(String(50))
    date = Column(DateTime(timezone= True))
    wordContent = Column(TEXT)
    sentiment = Column(Float, default = 0.0)
    state = Column(SQLEnum(ProcessState), default = ProcessState.PENDING) # pending 기본값, nlp 처리 후 completed 로 변경
    learning_state = Column(SQLEnum(LearningState), default = LearningState.PENDING)
    request_id = Column(String(50)) # 어떤 요청에서 수집된 데이터인지 추적하기 위한 필드
    __table_args__ = (
        UniqueConstraint('gallId', 'date', 'wordContent', name = 'id'),
    )

class WeightInWord(Base):
    __tablename__ = 'weights'
    id = Column(Integer, primary_key = True, index = True)
    word = Column(String(30))
    weight = Column(Float)
    update_count = Column(Integer, default = 0)

    __table_args__ = (
        UniqueConstraint('word', name = 'word'),
    )

class RequestLog(Base):
    __tablename__ = 'request_logs'
    id = Column(Integer, primary_key = True, index = True)
    request_id = Column(String(50), unique=True)
    gall_main_url = Column(String(255))
    days = Column(Integer)
    days_ago = Column(Integer)
    status = Column(SQLEnum(RequestStatus), default=RequestStatus.PENDING)
    error_message = Column(TEXT, nullable=True)
    saved_rows = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)

class AverageSentimentForOneDay(Base):
    __tablename__ = 'average_sentiments_for_one_day'
    id = Column(Integer, primary_key = True, index = True)
    gall_id = Column(String(50))
    date = Column(DateTime(timezone=True))
    average_sentiment = Column(Float)

    __table_args__ = (
        UniqueConstraint('gall_id', 'date', name = 'gall_id_date'),
    )
