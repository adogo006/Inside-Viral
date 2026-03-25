FROM python:3.10-slim
WORKDIR /crawling

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY ./.devcontainer/Scraping_env/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# uvicorn으로 서버 실행 (8002 포트)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]
