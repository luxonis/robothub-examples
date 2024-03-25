#!/bin/bash
set -e

export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:/opt/ros/humble/share/turtlebot3_gazebo/models
export LDS_MODEL=LDS-01
export TURTLEBOT3_MODEL=waffle
export ROS_DOMAIN_ID=30
export GAZEBO_MASTER_URI=http://localhost:11346

source "/opt/ros/humble/setup.bash"

P=$(pwd)

ros2 service call /map_saver/save_map nav2_msgs/srv/SaveMap '{"map_url": "'$P'/maps/'$1'"}'
