FROM ghcr.io/luxonis/robothub-app-v2:2023.183.1356-regular

RUN apt-get update && apt-get install -y git && \
    pip3 uninstall -y robothub_oak && \
    pip3 install -U git+https://github.com/luxonis/robothub-oak.git@develop && \
    apt-get remove -y git && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*
