from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from bs4 import BeautifulSoup
import time

from DB_manager.database import engine, SessionLocal
from DB_manager.models import Word, Base, ProcessState
from Crawling import startCrawler

app = FastAPI(title= 'inside-viral Crawler Service')

class CrawlerRequest(BaseModel):
    url: str
    days : int

def task_crawl_and_save(url: str, days: int):
    print('(API)크롤링을 시작합니다.')
    Words = startCrawler(url, days)
    db = SessionLocal()