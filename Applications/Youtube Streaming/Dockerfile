FROM ghcr.io/luxonis/robothub-app-v2:2024.022.1650-rvc2-regular

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
