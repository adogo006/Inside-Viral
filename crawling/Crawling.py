#!!!!!반드시 vpn 키고 돌릴것!!!!!
from urllib.request import urlopen, Request
from urllib.request import HTTPError
from urllib.request import URLError
from DB_manager.database import SessionLocal

from bs4 import BeautifulSoup
from datetime import datetime
import time
from random import randint
from crud_crawling import save_in_database


# html 내부 div 태그 class 속성 view_content_wrap 내부에서 제목 글 시간 모두 크롤링 가능 
# 
# 본문의 제목 크롤링 함수, 1.기간내의 게시물인지 확인 2. 제목과 게시글 파싱 및 단어리스트 반환
def contentCrawler(Words: list, gallId: str, dataNum: str, firstUrl: str, now: datetime, period: int):
    current_no = int(dataNum)
    
    while 1 :
        time.sleep(0.1 * randint(1, 4))  
        if len(Words) >= 100:
            db = SessionLocal()
            save_in_database(db, Words)
            db.close()
            Words.clear()
            print('데이터 저장 후 리스트를 비웠습니다.')

        try:
            url = 'https://gall.dcinside.com/' + firstUrl.rsplit('/', 1)[0] + '/?id={}&no={}&page1'.format(gallId, current_no)
            req = Request(url, headers= {'User-Agent': 'Mozilla/5.0'})
            html = urlopen(req)
        except HTTPError as e:
            current_no -= 1
            continue
        except URLError as e:
            print('URL에러! 서버와 통신이 안 됨! 강제종료!: {e}')
            return -1
        else:
            current_no -=1
            print('........크롤링 중........')

        bs = BeautifulSoup(html, 'html.parser')
        contentWrap = bs.find('div', {'class': 'view_content_wrap'})

        if contentWrap is None:
            print('파싱 실패! 다음 글로 넘어갑니다!')
            continue
        upTime = contentWrap.find('span', {'class': 'gall_date'})
        #만약 삭제된 게시글이라 upTime이 None이 지정되면 다음 게시글로 이동해서 파싱
        if upTime == None:
            print('파싱 실패! 다음 글로 넘어갑니다!')
            continue
        
        upTimeTitle = upTime.attrs['title']
        dt = datetime.strptime(upTimeTitle, "%Y-%m-%d %H:%M:%S")
        diff = now - dt
        if diff.days < period:
            title = contentWrap.find('span', {'class': 'title_subject'}).get_text(strip = True)
            print(title)   
            # Words.append({"gallId": f"{gallId}", "wordContent": f"{title}", "date": f"{dt}"})

            writeDivP = contentWrap.find('div', {'class':'write_div'})
            article = writeDivP.get_text(separator= " ", strip= True)
            titleArticle = title + ' ' + article
            Words.append({"gallId": f"{gallId}", "wordContent": f"{titleArticle}", "date": f"{dt}"})
            print(article) 
            continue  
            
        else:
            db = SessionLocal()
            save_in_database(db, Words)
            db.close()
            Words.clear()
            print('크롤링을 성공적으로 종료합니다!')
            break


# 메인 목록 안 bs에서 최근 게시글의 url과 업로드 시간을 가져오고 현재시간과 비교한 후 최근 게시글의 gallid 랑 게시글인덱스 반환 
def firstListParsing(bs, now, period):
    
    list = bs.find('tr', {'class': 'ub-content us-post', 'data-type': ['icon_txt', 'icon_pic']})
    if list == None:
        print('list 파싱 에러')
        return -1
    #만약 삭제된 게시글이라 upTime이 None이 지정되면 다음 게시글로 이동해서 파싱
    
    upTime = list.find('td', {'class': 'gall_date'})
    if upTime == None:
        print('upTime 파싱 에러')
        return -1
    
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
        print('최근 {}일 내의 게시물 이 없습니다!'.format(period))
        return -1

#!!!!!반드시 vpn 키고 돌릴것!!!!!
# url과 시간을 받으면 그 시간안에 메인페이지 안에 있는 모든 게시글과 내용을 받음
def startCrawler(initUrl:str, days: int):
    now = datetime.now()
    period = days #{perid}일 기준 이내 게시글 크롤링
    # 메인페이지 url로 html 파싱 시작
    url = initUrl
    req = Request(url, headers= {'User-Agent': 'Mozilla/5.0'})
    html = urlopen(req)
    bs = BeautifulSoup(html, 'html.parser')
    Words = []
    # 크롤링 시점 기준 가장 최근 게시글 파싱 함수 ; 리턴 : gallid, 게시글번호 ; 만약, 설정한 기간내의 게시글이 없을때 -1 반환
    fLP = firstListParsing(bs, now, period)
    if fLP==-1:
        print('크롤링 실패! 프로세스를 종료합니다.')
        return Words;    
    contentCrawler(Words, fLP[0], fLP[1], fLP[2], now, period)
    return Words;

# if __name__ == "__main__":
#     main()
