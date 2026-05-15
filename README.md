# 작업방식의 변화

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

---

# 웹사이트 디자인
DB에서 일 별 sentiment, 해당 gall_id 가져오기
리스트에 저장 후 그래프로 표현

웹 개발 몰라서 온전히 바이브코딩

CLAUDE.md 를 작성하여 session과 토큰 관리하는 법 학습 필요

<img src="./happy.gif" alt="대 호 황" style="max-width: 100%; border-radius: 10px;">
<img src="./sad.gif" alt="대 곰 탕" style="max-width: 100%; border-radius: 10px;">

---

# DB에 NLP 기능 연결 구현

main.py : connect api, control session, call feature
crud_NLP.py : connect DB, deal with all task about DB
KeywordExtractor.py : extract keyword with weights
SentimentAnalyzer.py : set sentiment of sentences, using weights
download_models.py : download NLP models

### flow
when container open, run download_models.py
main.py get api
call extract_keyword()
	open session
		get sentences on DB
		calculate weights
		update weight table
	close session
call assign_sentiment()
	open session
		get sentences on DB
		get saved weights on DB
		analyze final sentiment of each sentences
	close session