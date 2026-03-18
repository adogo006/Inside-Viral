from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from bs4 import BeautifulSoup
import time

from DB_manager.database import engine, SessionLocal
from DB_manager import models
from Crawling import startCrawler
from crud_crawling import save_in_database

app = FastAPI(title= 'inside-viral Crawler Service')

class CrawlerRequest(BaseModel):
    url: str
    days : int

def task_crawl_and_save(url: str, days: int):
    models.Base.metadata.create_all(bind = engine)
    print('(API)크롤링을 시작합니다.')
    Words = startCrawler(url, days)
    db = SessionLocal()
    
    save_in_database(db, Words)

    db.close()



if __name__ == '__main__':
     task_crawl_and_save('https://gall.dcinside.com/mgallery/board/lists?id=github', 1)