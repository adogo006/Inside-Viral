from urllib.request import urlopen, Request
from urllib.request import HTTPError
from urllib.request import URLError

import re

from bs4 import BeautifulSoup

def urlCrawler(url):
    #브라우저인척 유저 에이전트 헤더를 설정함
    req = Request(url, headers= {'User-Agent': 'Mozila/5.0'})
    html = urlopen(req)
    bs = BeautifulSoup(html, 'html.parser')
    #html 에서 a 태그를 가져온다. 이때 속성값으로 href 를 가지면 그걸 출력한다.
    #href 속성은 링크가 연결될 목적지를 값으로 가진다.
    for link in bs.find_all('a'):
        if 'href' in link.attrs:
            print(link.attrs['href'])

def urlCrawler2(url):
    req = Request(url, headers= {'User-Agent': 'Mozila/5.0'})
    html = urlopen(req)
    bs = BeautifulSoup(html, 'html.parser')
    for link in bs.find('div', {'id': 'bodyContent'}).find_all('a', {'href': re.compile('^(/wiki/)((?!:).)*$')}):
        if 'href' in link.attrs:
            print(link.attrs['href'])

def getLinks(articleUrl):
    req = Request(articleUrl, headers= {'User-Agent': 'Mozila/5.0'})
    html = urlopen(req)
    bs = BeautifulSoup(html, 'html.parser')

    return bs.find('div', {'id': 'bodyContent'}).find_all('a', {'href': re.compile('^(/wiki/)((?!:).)*$')})


def main():
    links = getLinks('https://en.wikipedia.org/wiki/Kevin_Bacon')
    while len(links) > 0 :
        newArticle = links[random.randint(0, len(links)-1)].attrs['href']
        print(newArticle)
        links = getLinks(newArticle)

if __name__ == "__main__":
    main()
