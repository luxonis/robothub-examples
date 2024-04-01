#!/bin/bash
set -e

source "/opt/ros/humble/setup.bash"

ros2 launch nav2_bringup tb3_simulation_launch.py slam:=True use_rviz:=False
