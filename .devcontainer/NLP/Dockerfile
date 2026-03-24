FROM python:3.11-bookworm

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src

COPY ./.devcontainer/NLP/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 모델들이 저장될 전용 폴더 주소를 선언합니다.
ENV TRANSFORMERS_CACHE=/root/.cache/huggingface
ENV SENTENCE_TRANSFORMERS_HOME=/root/.cache/torch/sentence_transformers

COPY . .

RUN python3 src/download_models.py
