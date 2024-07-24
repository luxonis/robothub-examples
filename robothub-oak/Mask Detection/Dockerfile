FROM ghcr.io/luxonis/robothub-app-v2:2023.108.0914-regular

RUN apt-get update && apt-get install -y git
RUN pip3 uninstall -y depthai_sdk robothub_oak
RUN pip3 install -U git+https://github.com/luxonis/depthai.git@develop#subdirectory=depthai_sdk
RUN pip3 install -U git+https://github.com/luxonis/robothub-oak.git@develop