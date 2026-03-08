from urllib.request import urlopen, Request
from urllib.request import HTTPError
from urllib.request import URLError

import re

from bs4 import BeautifulSoup
import json
# url을 통해 접속하고 각 단어를 리턴하는 함수
#일단 게시글 안에서는 script 태그 안 속성  'type': 'application/ld+json' 안에 시간 내용 제목 다 들어가 있음

def contentCrawler(url):
    req = Request(url, headers= {'User-Agent': 'Mozila/5.0'})
    html = urlopen(req)
    bs = BeautifulSoup(html, 'html.parser')
    content = bs.find('script', {'type': 'application/ld+json'})
    data = json.loads(content.string)
    title = data.get("headline")
    articleBody = data.get("articleBody")
    titleList = title.rsplit("-", 1)[0].strip().split(" ")
    articleBodyList = articleBodyParser(articleBody)

    for s in titleList:
        print(s)
    for s in articleBodyList:
        print(s)

def articleBodyParser(articleBody):
    suffix = "- dc official App"
    if articleBody.endswith(suffix):
        articleBody = articleBody[:-len(suffix)]
    articleBodyList = articleBody.strip().split(" ")
    return articleBodyList


def main():
    contentCrawler('https://gall.dcinside.com/mgallery/board/view/?id=stockus&no=14603145&exception_mode=recommend&page=1')


if __name__ == "__main__":
    main()
