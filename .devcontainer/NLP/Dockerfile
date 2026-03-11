FROM mcr.microsoft.com/devcontainers/python:1-3.11-bullseye

RUN rm -f /etc/apt/sources.list.d/yarn.list \
    && apt-get update && apt-get clean -y && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir soynlp numpy pandas