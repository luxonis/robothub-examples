FROM ghcr.io/luxonis/robothub-app-v2:2023.183.1356-regular

RUN apt update && apt install -y git
RUN python3.10 -m pip uninstall -y robothub-oak && \
    python3.10 -m pip install --no-deps --no-cache-dir git+https://github.com/luxonis/robothub-oak.git@develop && \
    python3.10 -m pip install --no-deps --no-cache-dir git+https://github.com/luxonis/depthai.git@fix/encoded_tracker#subdirectory=depthai_sdk
