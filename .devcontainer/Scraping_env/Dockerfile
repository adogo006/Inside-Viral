FROM python:3.10-slim
WORKDIR /crawling

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY ./.devcontainer/scraping_env/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . .


