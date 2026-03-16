#실행 파일 (FAST_API 및 단순실행)
import psycopg2
import os
from dotenv import load_dotenv


try:
    conn = psycopg2.connect(
        host = "localhost",
        database = "insideViral_db",
        user = "inside",
        password = "Viral",
        port = 5432
    )
    print("DB 연결 성공!")

except Exception as e:
    print("연결 실패: {}".format(e))

cursor = conn.cursor()

create_table_qurey = """
CREATE TABLE IF NOT EXISTS words (
    id SERIAL PRIMARY KEY,
    gallId VARCHAR(50),
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    wordContent VARCHAR(500),
    sentiment FLOAT
    );
"""

cursor.execute(create_table_qurey)
conn.commit()
print("테이블 생성 완료!")

if 'cursor' in locals(): cursor.close()
if 'conn' in locals(): conn.close()