FROM ghcr.io/luxonis/robothub-app-v2:2023.131.2203-regular

RUN apt-get update -y && \
    apt-get install -y git

RUN pip install --upgrade pip
RUN pip install git+https://github.com/luxonis/depthai.git@camera-app#subdirectory=depthai_sdk
RUN pip install --upgrade git+https://github.com/whoactuallycares/robothub-oak.git@camera-app