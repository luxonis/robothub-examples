FROM ros:humble-ros-core

COPY requirements.txt /tmp

RUN apt update && \
    apt install -y python3-pip && \
    apt install -y ros-humble-navigation2 && \
    apt install -y ros-humble-nav2-bringup && \
    apt install -y ros-humble-turtlebot3-gazebo && \
    apt install -y ros-humble-turtlebot3-bringup && \
    apt install -y ros-humble-slam-toolbox && \
    apt install -y ros-humble-robot-state-publisher && \
    pip3 install -r /tmp/requirements.txt

WORKDIR /project

CMD ["bash", "entrypoint.sh"]
