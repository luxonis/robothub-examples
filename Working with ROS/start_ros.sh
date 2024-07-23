#!/bin/bash
set -e

# setup ros environment
source "/opt/ros/$ROS_DISTRO/setup.bash"
source "/ws/install/setup.bash"

export ROS_DOMAIN_ID=30 # setup domain id
# Add your custom launch file here 
# ros2 launch demo_nodes_cpp talker_listener.launch.py 