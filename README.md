## DB에 NLP 기능 연결 구현

main.py : connect api, control session, call feature
crud_NLP.py : connect DB, deal with all task about DB
KeywordExtractor.py : extract keyword with weights
SentimentAnalyzer.py : set sentiment of sentences, using weights
download_models.py : download NLP models

### flow
when container open, run download_models.py
main.py get api
call extract_keyword()
	open session to give session as parameter
	call crud_NLP.py get_words(Session)
		get data on DB as list
		call KeywordExtractor.py main(list)

	close session
call assign_sentiment()
	open session to give session as parameter

---

## 작업방식의 변화

### AI Agent 사용

Claude Code framework에 ollama 제공 cloud model을 실행

1. Claude Code, Git Bash, Ollama 설치
2. 시스템 환경 설정 Path 추가
3. VS Code에 "Claude Code for VS Code" Extension install
4. terminal에서 claude 실행
5. ctrl + c
6. ollama model 실행 코드 입력

model 실행 코드 예시
ollama launch claude --model qwen3.5:cloud
ollama launch claude --model minimax-m2.7:cloud