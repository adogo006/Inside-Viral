from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import time

from Crawling import startCrawler
# from common.database import SessionLocal
# from common import crud

app = FastAPI(title= 'inside-viral Crawler Service')

class CrawlerRequest(BaseModel):
    url: str
    days : int

def task_crawl_and_save(url: str, days: int):
    print('(API)크롤링을 시작합니다.')