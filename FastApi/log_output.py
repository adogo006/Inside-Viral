from datetime import datetime

# 메모리에 로그를 저장할 리스트 (최대 200줄 유지)
GLOBAL_LOGS = []

def add_log(msg: str):
    now = datetime.now().strftime("%H:%M:%S")
    formatted_msg = f"[{now}] {msg}"
    
    # 1. 터미널(콘솔)에 기존처럼 출력
    print(formatted_msg)
    
    # 2. 메모리 배열에 저장 (HTML로 보내기 위함)
    GLOBAL_LOGS.append(formatted_msg)
    
    # 너무 길어지면 오래된 로그 삭제
    if len(GLOBAL_LOGS) > 200:
        GLOBAL_LOGS.pop(0)