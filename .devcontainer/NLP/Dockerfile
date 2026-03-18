FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /NLP

COPY requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

RUN python3 -c "\
from transformers import AutoTokenizer, AutoModelForSequenceClassification; \
from sentence_transformers import SentenceTransformer; \
\
model_name = 'jaehyeong/koelectra-base-v3-generalized-sentiment-analysis'; \
AutoTokenizer.from_pretrained(model_name); \
AutoModelForSequenceClassification.from_pretrained(model_name); \
\
sbert_model = 'snunlp/KR-SBERT-V40K-klueNLI-augSTS'; \
SentenceTransformer(sbert_model)"

COPY . .