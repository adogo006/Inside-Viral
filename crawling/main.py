from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import time

from Crawling import startCrawler
# from common.database import SessionLocal
# from common import crud

app = FastAPI(title= 'inside-viral Crawler Service')

class CrawlerRequest(BaseModel):
    url: str
    period : int

def task_crawl_and_save