FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/usr/local/bin:${PATH}"

WORKDIR /NLP

COPY ./.devcontainer/NLP_env/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 모델들이 저장될 전용 폴더 주소를 선언합니다.
ENV TRANSFORMERS_CACHE=/root/.cache/huggingface
ENV SENTENCE_TRANSFORMERS_HOME=/root/.cache/torch/sentence_transformers

COPY . .

RUN python3 NLP/download_models.py

#uvicorn으로 서버 실행 (8001 포트)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]