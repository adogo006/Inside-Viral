FROM mcr.microsoft.com/devcontainers/python:1-3.11-bullseye

RUN rm -f /etc/apt/sources.list.d/yarn.list \
    && apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get install -y --no-install-recommends \
    default-jdk \
    g++ \
    build-essential \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir konlpy jamo soynlp