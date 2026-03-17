--table 삭제
DROP TABLE words;

--table의 자료 객체 크기 조정
ALTER TABLE words ALTER COLUMN "wordContent" TYPE VARCHAR(500);