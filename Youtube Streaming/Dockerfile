FROM ghcr.io/luxonis/robothub-app-v2:2023.183.1356-regular

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*