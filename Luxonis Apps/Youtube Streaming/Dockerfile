FROM ghcr.io/luxonis/robothub-app-v2:2024.110.1321-rvc2-regular

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
