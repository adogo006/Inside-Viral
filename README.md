DB에 NLP 기능 연결 구현

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

model 실행 코드 예시 : ollama launch claude --model qwen3.5