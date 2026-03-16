FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /NLP

COPY .devcontainer/NLP/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

#컨테이너 실행 시 매번 다운로드하지 않도록 모델을 빌드 시점에 설치

COPY . .