FROM ghcr.io/luxonis/robothub-app-v2:2023.218.1205-regular

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
