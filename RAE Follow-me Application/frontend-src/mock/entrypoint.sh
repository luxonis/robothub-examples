#!/bin/bash
set -e

export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:/opt/ros/humble/share/turtlebot3_gazebo/models
export LDS_MODEL=LDS-01
export TURTLEBOT3_MODEL=waffle
export ROS_DOMAIN_ID=30
export GAZEBO_MASTER_URI=http://localhost:11346

source "/opt/ros/humble/setup.bash"

python3 backend.py & ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py  & wait -n
