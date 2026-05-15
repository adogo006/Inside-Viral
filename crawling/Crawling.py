#!!!!!반드시 vpn 키고 돌릴것!!!!!
import httpx
import asyncio
from DB_manager.database import SessionLocal

from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from random import randint
import importlib
from crud_crawling import save_in_database

try:
    from crawling import runtime_state
except ImportError:
    runtime_state = importlib.import_module('runtime_state')



# 다양한 User-Agent 헤더 리스트 정의
REQUEST_HEADERS_LIST = [
    # 1. Windows - Chrome (최신 버전 반영)
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1'
    },
    # 2. macOS - Safari (최신 버전 반영)
    {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/19.0 Safari/605.1.15',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    },
    # 3. Windows - Edge (새로운 메이저 브라우저 추가)
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none'
    },
    # 4. Windows - Firefox (최신 버전 반영)
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    },
    # 5. Linux - Chrome (최신 버전 반영)
    {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
]


def crawler_log(message: str, request_id: str | None = None, gallId: str | None = None):
    if gallId is not None:
        print(f"[Crawler:{gallId}] {message}")
    else:
        print(f"[Crawler] {message}")


def dynamic_sleep_seconds(min_unit: int, max_unit: int) -> float:
    active = max(0, min(runtime_state.active_tasks, runtime_state.MAX_CONCURRENT_TASKS))
    load_ratio = active / runtime_state.MAX_CONCURRENT_TASKS
    # 활성 작업이 적을수록 더 빠르게 가져오고, 5개일 때는 기존 딜레이를 그대로 유지
    scale = 0.4 + (0.6 * load_ratio)
    return (0.1 * randint(min_unit, max_unit)) * scale


# html 내부 div 태그 class 속성 view_content_wrap 내부에서 제목 글 시간 모두 크롤링 가능 
# 
# 본문의 제목 크롤링 함수, 1.기간내의 게시물인지 확인 2. 제목과 게시글 파싱 및 단어리스트 반환
async def contentCrawler(Words: list, gallId: str, dataNum: str, firstUrl: str, now: datetime, period: int, request_id: str | None = None):

    current_no = int(dataNum)
    save_count = 0

    # 반복문에서 사용할 헤더를 랜덤으로 하나 선택
    selected_headers = REQUEST_HEADERS_LIST[randint(0, len(REQUEST_HEADERS_LIST)-1)]

    async with httpx.AsyncClient() as client:
        while 1:
            await asyncio.sleep(dynamic_sleep_seconds(10, 30))
            if len(Words) >= 100:
                db = SessionLocal()
                try:
                    save_in_database(db, Words)
                except Exception as e:
                    crawler_log(f'데이터 저장 중 오류 발생: {e}', request_id, gallId)
                finally:
                    db.close()
                Words.clear()
                save_count += 1
                crawler_log('데이터 저장 후 리스트를 비웠습니다.', request_id, gallId)

            try:
                url = 'https://gall.dcinside.com' + firstUrl.rsplit('/', 1)[0] + '/?id={}&no={}&page1'.format(gallId, current_no)
                response = await client.get(url, headers=selected_headers)
                response.raise_for_status()
                html = response.text 
            except httpx.HTTPStatusError as e:
                current_no -= 1
                continue
            except httpx.RequestError as e:
                crawler_log(f'URL에러! 서버와 통신이 안 됨! 강제종료!: {e}', request_id, gallId)
                return -1, save_count
            else:
                current_no -= 1
                crawler_log(f'........크롤링 중........({len(Words)} / 100)', request_id, gallId)

            bs = BeautifulSoup(html, 'html.parser')
            contentWrap = bs.find('div', {'class': 'view_content_wrap'})

            if contentWrap is None:
                if not html or len(html.strip()) < 500:
                    crawler_log('IP 차단이 의심됩니다.', request_id, gallId)
                    return -1, save_count

                crawler_log('파싱 실패! 다음 글로 넘어갑니다!', request_id, gallId)
                await asyncio.sleep(dynamic_sleep_seconds(20, 40))
                continue
            upTime = contentWrap.find('span', {'class': 'gall_date'})
            #만약 삭제된 게시글이라 upTime이 None이 지정되면 다음 게시글로 이동해서 파싱
            if upTime == None:
                crawler_log('파싱 실패! 다음 글로 넘어갑니다!', request_id, gallId)
                await asyncio.sleep(dynamic_sleep_seconds(20, 40))
                continue

            upTimeTitle = upTime.attrs['title']
            dt = datetime.strptime(upTimeTitle, "%Y-%m-%d %H:%M:%S")
            dt = dt.replace(tzinfo=timezone(timedelta(hours=9)))
            diff = now - dt
            if diff.days < period:
                title = contentWrap.find('span', {'class': 'title_subject'}).get_text(strip=True)
                crawler_log(f'제목: {title}', request_id, gallId)
                # Words.append({"gallId": f"{gallId}", "wordContent": f"{title}", "date": f"{dt}"})

                writeDivP = contentWrap.find('div', {'class': 'write_div'})
                article = writeDivP.get_text(separator=" ", strip=True)
                titleArticle = title + ' ' + article
                Words.append({"gallId": f"{gallId}", "wordContent": f"{titleArticle}", "date": f"{dt}", "request_id": f"{request_id}"})
                crawler_log(f'본문: {article}', request_id, gallId)
                continue

            else:
                db = SessionLocal()
                try:
                    save_in_database(db, Words)
                except Exception as e:
                    crawler_log(f'데이터 저장 중 오류 발생: {e}', request_id, gallId)
                finally:
                    db.close()
                Words.clear()
                crawler_log('크롤링을 성공적으로 종료합니다!', request_id, gallId)
                return 0, save_count


# 메인 목록 안 bs에서 최근 게시글의 url과 업로드 시간을 가져오고 현재시간과 비교한 후 최근 게시글의 gallid 랑 게시글인덱스 반환 
async def firstListParsing(initUrl: str, now: datetime, previousDays: int, request_id: str | None = None):
    errorPoint = 0
    count = 1
    url = initUrl
    selected_headers = REQUEST_HEADERS_LIST[randint(0, len(REQUEST_HEADERS_LIST)-1)]
    async with httpx.AsyncClient() as client:
        # 초기 메인 페이지 요청: 가장 최근 게시글 정보를 얻는다.
        while True:
            try:
                response = await client.get(url, headers=selected_headers)
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                crawler_log(f'첫 게시글을 여는데 문제가 생겼습니다. 다시 시도하겠습니다! HTTP 상태 코드: {e.response.status_code}', request_id)
                errorPoint += 1
                client.cookies.clear()
                selected_headers = REQUEST_HEADERS_LIST[randint(0, len(REQUEST_HEADERS_LIST)-1)]
                await asyncio.sleep(dynamic_sleep_seconds(10, 30))
                continue

            html = response.content
            bs = BeautifulSoup(html, 'html.parser')
            initList = bs.find('tr', {'class': 'ub-content us-post', 'data-type': ['icon_txt', 'icon_pic']})
            if initList is None:
                crawler_log(f'첫 게시글을 여는데 문제가 생겼습니다. 다시 시도하겠습니다.', request_id)
                errorPoint += 1
                if errorPoint >= 10:
                    crawler_log('첫 게시글을 여는데 계속 문제가 생깁니다. 크롤링을 종료합니다.', request_id)
                    return -1
                else:
                    client.cookies.clear()
                    selected_headers = REQUEST_HEADERS_LIST[randint(0, len(REQUEST_HEADERS_LIST)-1)]
                    await asyncio.sleep(dynamic_sleep_seconds(10, 30))
                    continue
            break
        
        dataNum = int(initList.attrs['data-no'])
        maxDataNum = dataNum
        minDataNum = 1

        # exact match를 못 찾더라도 가장 근접한 글 번호를 기억해서 fallback으로 사용
        best_data_num = dataNum
        best_diff_gap = float('inf')

        url = initList.find('a').attrs['href'] 
        url2 = url.rsplit('/', 1)[0]
        gallId = bs.find('button',{'id':'headTail_tab_gall'}).find('p',{'class': 'gallname'}).attrs['data-gallid']

        # 이진탐색: 원하는 날짜에 가장 근접한 게시글을 찾는다.
        while True:
            await asyncio.sleep(dynamic_sleep_seconds(10, 30))
            mid_data_num = (minDataNum + maxDataNum) // 2

            if mid_data_num <= minDataNum or mid_data_num >= maxDataNum:
                crawler_log('해당하는 날짜의 게시글을 찾지 못했습니다. 가장 가까운 게시글로 대체합니다.', request_id)
                fallback_url = 'https://gall.dcinside.com/' + url2 + '/?id={}&no={}&page=1'.format(gallId, best_data_num)
                return gallId, best_data_num, fallback_url.split('/', 3)[3]

            while errorPoint < 50 and count < 120:
                try:
                    url = 'https://gall.dcinside.com/' + url2 + '/?id={}&no={}&page=1'.format(gallId, mid_data_num)
                    response = await client.get(url, headers=selected_headers)
                    response.raise_for_status()
                    html = response.content
                    break
                except httpx.HTTPStatusError:
                    crawler_log(f'삭제되거나 존재하지 않는 게시글입니다. 탐색을 계속합니다!', request_id)
                    client.cookies.clear()
                    mid_data_num -= 1
                    count += 1
                    await asyncio.sleep(dynamic_sleep_seconds(10, 30))
                    continue
                except httpx.RequestError as e:
                    crawler_log(f'요청 에러 발생: {e}', request_id)
                    mid_data_num -= 1
                    count += 1
                    await asyncio.sleep(dynamic_sleep_seconds(10, 30))
                    continue
            
            if errorPoint > 50 or count > 120:
                if best_diff_gap != float('inf'):
                    fallback_url = 'https://gall.dcinside.com/' + url2 + '/?id={}&no={}&page=1'.format(gallId, best_data_num)
                    crawler_log(f'정확 일치 실패. 가장 근접한 게시글로 대체합니다. dataNum: {best_data_num}, 차이: {best_diff_gap}일', request_id)
                    return gallId, best_data_num, fallback_url.split('/', 3)[3]

                crawler_log('해당하는 날짜의 게시글을 불러오지 못했습니다!', request_id)
                return -1

            count += 1
            crawler_log(f'해당하는 날짜의 게시글 찾는 중... 반복횟수: {count}번, 현재 dataNum: {mid_data_num}, 에러횟수: {errorPoint}번', request_id)
            bs = BeautifulSoup(html, 'html.parser')
            upTime = bs.find('span', {'class': 'gall_date'})

            if upTime == None:
                mid_data_num -= 1
                errorPoint += 1
                continue
                
            upTimeTitle = upTime.attrs['title']
            dt = datetime.strptime(upTimeTitle, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone(timedelta(hours=9)))
            diffDays = (now - dt).days
            crawler_log(f'차이 일수: {diffDays}일', request_id)
            current_gap = abs(diffDays - previousDays)
            if current_gap < best_diff_gap:
                best_diff_gap = current_gap
                best_data_num = mid_data_num

            if diffDays > previousDays:
                #찾을려는 게시글보다 더 이전의 글이므로 dataNum(미국주식갤러리 같은 경우에는 현재 1400만) 증가 
                # diffDays 랑 previousDays 차이가 큰경우 크게
                minDataNum = mid_data_num
                continue
            elif diffDays < previousDays:
                #찾을려는 게시글보다 더 이 후의 글이므로 dataNum 감소 필요
                maxDataNum = mid_data_num
                continue
            else:    
                crawler_log(f'탐색성공! 탐색횟수 {count}번, {url}', request_id)
                return gallId, mid_data_num, url.split('/', 3)[3]

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
