# Working with ROS

This application demonstrates how to set up ROS working environment.

## Setup

Application should use Docker image that has ROS preinstalled (or installs it as specified in custom Dockerfile). This can be for example one of the official ROS images.
To enable visibility of ROS system libraries while running the App, you can update `pre_launch` configuration in `robotapp.toml` in following way:
`pre_launch = "export ROS_DOMAIN_ID=30\n. /opt/ros/$ROS_DISTRO/setup.sh\n. /ws/install/setup.sh"`
- `export ROS_DOMAIN_ID=30` - setting up correct ROS domaind ID when running
- `. /opt/ros/$ROS_DISTRO/setup.sh` - sourcing main ROS install
- `. /ws/install/setup.sh` - sourcing custom ROS package

In the App itself you can either create your own Python nodes via rclpy, or launch other nodes, for example via using separate bash script.