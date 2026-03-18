from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from DB_manager.database import engine
from DB_manager import models
from Crawling import startCrawler
from crud_crawling import export_to_txt

app = FastAPI(title= 'inside-viral Crawler Service')

class CrawlerRequest(BaseModel):
    url: str
    days : int

def task_crawl_and_save(url: str, days: int):
    models.Base.metadata.create_all(bind = engine)
    print('(API)크롤링을 시작합니다.')
    Words = startCrawler(url, days)
    print('(API)크롤링을 종료합니다.')



if __name__ == '__main__':
    # task_crawl_and_save('https://gall.dcinside.com/mgallery/board/lists?id=stockus', 7)
    export_to_txt()