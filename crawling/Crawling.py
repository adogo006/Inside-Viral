#!!!!!반드시 vpn 키고 돌릴것!!!!!
from urllib.request import urlopen, Request
from urllib.request import HTTPError
from urllib.request import URLError

import re

from bs4 import BeautifulSoup
from datetime import datetime
import time
from random import randint
# html 내부 div 태그 class 속성 view_content_wrap 내부에서 제목 글 시간 모두 크롤링 가능 
# write_div
# 본문의 제목 크롤링 함수, 1.기간내의 게시물인지 확인 2. 제목과 게시글 파싱 및 단어리스트 반환
def contentCrawler(words, gallId, dataNum, firstUrl, now, period):
    print('크롤링 중...')
    time.sleep(0.01 * randint(1, 3))
    # url 형식이 갤러리마다 다름 첫 링크 받아올때 받은걸로 수정 필요!
    url = 'https://gall.dcinside.com/' + firstUrl.rsplit('/', 1)[0] + '/?id={}&no={}&page1'.format(gallId, dataNum)
 
    try:
        req = Request(url, headers= {'User-Agent': 'Mozilla/5.0'})
        html = urlopen(req)
    except HTTPError as e:
        return contentCrawler(words, gallId, int(dataNum)-1, firstUrl, now, period)
    except URLError as e:
        print('서버와 통신이 안 됨! 강제종료!')
        return -1
    else:
        print('url 접속 성공!')
        pass
    bs = BeautifulSoup(html, 'html.parser')

    contentWrap = bs.find('div', {'class': 'view_content_wrap'})
    if contentWrap is None:
        print('파싱 실패! 다음 글로 넘어갑니다!')
        return contentCrawler(words, gallId, int(dataNum)-1, firstUrl, now, period)
    upTime = contentWrap.find('span', {'class': 'gall_date'})
    #만약 삭제된 게시글이라 upTime이 None이 지정되면 다음 게시글로 이동해서 파싱
    if upTime == None:
        return contentCrawler(words, gallId, int(dataNum)-1, firstUrl, now, period)
    
    upTimeTitle = upTime.attrs['title']

    dt = datetime.strptime(upTimeTitle, "%Y-%m-%d %H:%M:%S")
    diff = now - dt
    if diff.days <= period:
        title = contentWrap.find('span', {'class': 'title_subject'}).get_text(strip = True)
        print('제목: ', title)
        words.extend(title.split())
        writeDivP = contentWrap.find('div', {'class':'write_div'}).find_all('p')
        for p in writeDivP:
            article = p.get_text(strip = True)
            print('내용: ',article)
            words.extend(article.split())
        return contentCrawler(words, gallId, int(dataNum)-1, firstUrl, now, period)        
    else:
        return



# 메인 목록 안 bs에서 최근 게시글의 url과 업로드 시간을 가져오고 현재시간과 비교한 후 최근 게시글의 gallid 랑 게시글인덱스 반환 
def firstListParsing(bs, now, period):
    
    list = bs.find('tr', {'class': 'ub-content us-post', 'data-type': ['icon_txt', 'icon_pic']})
    if list == None:
        print('list 파싱 문제!')
        return -1
    #만약 삭제된 게시글이라 upTime이 None이 지정되면 다음 게시글로 이동해서 파싱
    
    upTime = list.find('td', {'class': 'gall_date'})
    # if upTime == None:
    #     print('upTime 파싱 문제!')
    #     return -1
    
    upTimeTitle = upTime.attrs['title']
    dt = datetime.strptime(upTimeTitle, "%Y-%m-%d %H:%M:%S")
    diff = now - dt
    if (diff.days <= period):
        firstNum = list.attrs['data-no']
        gallName = bs.find('button',{'id':'headTail_tab_gall'}).find('p',{'class': 'gallname'}).attrs['data-gallid']
        firstUrl = list.find('a').attrs['href']
        print('첫 게시글({}) 파싱 성공!'.format(gallName))
        return gallName, firstNum, firstUrl
    else:
        return -1

#!!!!!반드시 vpn 키고 돌릴것!!!!!
def main():
    now = datetime.now()
    period = 1 #{perid}일 기준 이내 게시글 크롤링
    # 메인페이지 url로 html 파싱 시작
    url ='https://gall.dcinside.com/mgallery/board/lists/?id=projectmx'
    req = Request(url, headers= {'User-Agent': 'Mozilla/5.0'})
    html = urlopen(req)
    bs = BeautifulSoup(html, 'html.parser')
    words= []
    # 크롤링 시점 기준 가장 최근 게시글 파싱 함수 ; 리턴 : gallid, 게시글번호 ; 만약, 설정한 기간내의 게시글이 없을때 -1 반환
    fLP = firstListParsing(bs, now, period)
    if fLP==-1:
        print('크롤링 실패! 해당되는 게시글이 없습니다.')
        return 0;    
    contentCrawler(words, fLP[0], fLP[1], fLP[2], now, period)

    for w in words:
        print(w)
    return 0;

if __name__ == "__main__":
    main()
