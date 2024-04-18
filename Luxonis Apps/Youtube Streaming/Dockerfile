FROM ghcr.io/luxonis/robothub-app-v2-dev:2024.109.1233-rvc2-regular

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
