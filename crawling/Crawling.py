#!!!!!반드시 vpn 키고 돌릴것!!!!!
import httpx
import asyncio
from DB_manager.database import SessionLocal

from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from random import randint
from crud_crawling import save_in_database


REQUEST_HEADERS = {'User-Agent': 'Mozilla/5.0'}


def crawler_log(message: str, request_id: str | None = None):
    print(f"[Crawler] {message}")


# html 내부 div 태그 class 속성 view_content_wrap 내부에서 제목 글 시간 모두 크롤링 가능 
# 
# 본문의 제목 크롤링 함수, 1.기간내의 게시물인지 확인 2. 제목과 게시글 파싱 및 단어리스트 반환
async def contentCrawler(Words: list, gallId: str, dataNum: str, firstUrl: str, now: datetime, period: int, request_id: str | None = None):
    current_no = int(dataNum)
    save_count = 0

    async with httpx.AsyncClient() as client:
        while 1 :
            await asyncio.sleep(0.1 * randint(1, 4))  
            if len(Words) >= 100:
                db = SessionLocal()
                save_in_database(db, Words)
                db.close()
                Words.clear()
                save_count += 1
                crawler_log('데이터 저장 후 리스트를 비웠습니다.', request_id)

            try:
                url = 'https://gall.dcinside.com' + firstUrl.rsplit('/', 1)[0] + '/?id={}&no={}&page1'.format(gallId, current_no)
                response = await client.get(url, headers=REQUEST_HEADERS)
                response.raise_for_status()
                html = response.text
            except httpx.HTTPStatusError as e:
                current_no -= 1
                continue
            except httpx.RequestError as e:
                crawler_log(f'URL에러! 서버와 통신이 안 됨! 강제종료!: {e}', request_id)
                return -1, save_count
            else:
                current_no -=1
                crawler_log(f'........크롤링 중........({len(Words)} / 100)', request_id)

            bs = BeautifulSoup(html, 'html.parser')
            contentWrap = bs.find('div', {'class': 'view_content_wrap'})

            if contentWrap is None:
                crawler_log('파싱 실패! 다음 글로 넘어갑니다!', request_id)
                continue
            upTime = contentWrap.find('span', {'class': 'gall_date'})
            #만약 삭제된 게시글이라 upTime이 None이 지정되면 다음 게시글로 이동해서 파싱
            if upTime == None:
                crawler_log('파싱 실패! 다음 글로 넘어갑니다!', request_id)
                continue
            
            upTimeTitle = upTime.attrs['title']
            dt = datetime.strptime(upTimeTitle, "%Y-%m-%d %H:%M:%S")
            dt = dt.replace(tzinfo=timezone(timedelta(hours=9)))
            diff = now - dt          
            if diff.days < period:
                title = contentWrap.find('span', {'class': 'title_subject'}).get_text(strip = True)
                crawler_log(f'제목: {title}', request_id)
                # Words.append({"gallId": f"{gallId}", "wordContent": f"{title}", "date": f"{dt}"})

                writeDivP = contentWrap.find('div', {'class':'write_div'})
                article = writeDivP.get_text(separator= " ", strip= True)
                titleArticle = title + ' ' + article
                Words.append({"gallId": f"{gallId}", "wordContent": f"{titleArticle}", "date": f"{dt}"})
                crawler_log(f'본문: {article}', request_id)
                continue  
                
            else:
                db = SessionLocal()
                save_in_database(db, Words)
                db.close()
                Words.clear()
                crawler_log('크롤링을 성공적으로 종료합니다!', request_id)
                return 0, save_count


# 메인 목록 안 bs에서 최근 게시글의 url과 업로드 시간을 가져오고 현재시간과 비교한 후 최근 게시글의 gallid 랑 게시글인덱스 반환 
async def firstListParsing(initUrl: str, now: datetime, previousDays: int, request_id: str | None = None):
    errorPoint = 0
    count = 1

    url = initUrl
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=REQUEST_HEADERS)
        html = response.content
        bs = BeautifulSoup(html, 'html.parser')
        initList = bs.find('tr', {'class': 'ub-content us-post', 'data-type': ['icon_txt', 'icon_pic']})
        if initList == None:
            crawler_log('첫 게시글을 여는데 문제가 생겼습니다.', request_id)
            return -1
        
        dataNum = int(initList.attrs['data-no'])
        maxDataNum = dataNum

        url = initList.find('a').attrs['href'] 
        url2 = url.rsplit('/', 1)[0]
        gallId = bs.find('button',{'id':'headTail_tab_gall'}).find('p',{'class': 'gallname'}).attrs['data-gallid']

        while 1:
            if errorPoint > 50 or count > 100:
                crawler_log('해당하는 날짜의 게시글을 불러오지 못했습니다!', request_id)
                return -1

            await asyncio.sleep(0.1 * randint(1,4))

            try:
                url = 'https://gall.dcinside.com/' + url2 + '/?id={}&no={}&page=1'.format(gallId, dataNum)
                response = await client.get(url, headers=REQUEST_HEADERS)
                response.raise_for_status()
                html = response.content
            except httpx.HTTPStatusError as e:
                print(f'HTTP 에러 발생: {e}')  
                client.cookies.clear()
                dataNum -= 1   
                errorPoint += 1
                continue
            except httpx.RequestError as e:
                print(f'요청 에러 발생: {e}')
                dataNum -= 1
                errorPoint += 1
                continue
            else:
                crawler_log(f'해당하는 날짜의 게시글 찾는 중... 반복횟수: {count}번, 현재 dataNum: {dataNum}, 에러횟수: {errorPoint}번', request_id)

            bs = BeautifulSoup(html, 'html.parser')
            upTime = bs.find('span', {'class': 'gall_date'})

            if upTime == None:
                dataNum -= 1
                errorPoint += 1
                continue
                
            upTimeTitle = upTime.attrs['title']
            dt = datetime.strptime(upTimeTitle, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone(timedelta(hours=9)))
            diffDays = (now - dt).days
            crawler_log(f'차이 일수: {diffDays}일', request_id)

            if diffDays > previousDays:
                #찾을려는 게시글보다 더 이전의 글이므로 dataNum(미국주식갤러리 같은 경우에는 현재 1400만) 증가 
                # diffDays 랑 previousDays 차이가 큰경우 크게
                dataNum += int((diffDays - previousDays)/(diffDays+previousDays) * (maxDataNum//(count+1)**2))
                count +=1
                continue
            elif diffDays < previousDays:
                #찾을려는 게시글보다 더 이 후의 글이므로 dataNum 감소 필요
                dataNum -= int((previousDays - diffDays)/(diffDays+previousDays) * (maxDataNum//(count+1)**2))
                count += 1
                continue
            else:    
                crawler_log(f'탐색성공! 탐색횟수 {count}번, {url}', request_id)
                return gallId, dataNum, url.split('/', 3)[3]

#!!!!!반드시 vpn 키고 돌릴것!!!!!
# url과 시간을 받으면 그 시간안에 메인페이지 안에 있는 모든 게시글과 내용을 받음
async def startCrawler(initUrl:str, days: int, previousDays: int = 0, request_id: str | None = None):
    now = datetime.now(timezone(timedelta(hours=9)))
    crawler_log(f'크롤링을 시작합니다! URL: {initUrl}, 기간: {days}일, 이전기간: {previousDays}일', request_id)
    period = days #{perid}일 기준 이내 게시글 크롤링
    # 메인페이지 url로 html 파싱 시작
    Words = []
    # 크롤링 시점 기준 가장 최근 게시글 파싱 함수 ; 리턴 : gallid, 게시글번호 ; 만약, 설정한 기간내의 게시글이 없을때 -1 반환
    fLP = await firstListParsing(initUrl, now, previousDays, request_id)
    if fLP==-1:
        crawler_log('크롤링 실패! 프로세스를 종료합니다.', request_id)
        return -1, 0  
    # 마지막인자는 {prviousDays} 일 후 {period} 일 기간 동안의 데이터를 크롤링한다는 의미
    isError, save_count = await contentCrawler(Words, fLP[0], fLP[1], fLP[2], now, period+previousDays, request_id)
    if isError == -1:
        return -1, save_count

    return 0, save_count
# if __name__ == "__main__":
#     asyncio.run(main())
