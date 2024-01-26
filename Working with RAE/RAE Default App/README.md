# RAE Default App

This is an example of Default RAE App source code. In this example, FollowMe Application is used as the default entry point, but others can be specified via `robotapp.toml` file.

## Features
- FollowMe Application - robot is put in a mode that follows a person standing in front or in the back of the robot
- A FrontEnd application is launched to publish images on LCD screen or control LED behavior
- Abstractions are provided for the robot class that allow customizing the App behavior, or creation of a whole different app
- It is possible to set up streams for both RobotHub using provided wrappers

## Requirements

- RAE

## Dependencies
- ROS2 Humble
- DepthAI libraries
- RobotHub

## Concepts of Robot classes

1. The Robot Class: An Integrated Approach to Robotics Control

The Robot class stands as a cornerstone in robotics control, encapsulating various functionalities such as movement, display, and LED control. This class serves as a bridge between hardware components and higher-level software commands, thereby streamlining robotics operations.

Key Functionalities:
- Movement Control: By integrating a MovementController, the Robot class allows for precise control over the robot's motion, enabling it to navigate its environment effectively.
- Visual Feedback: The incorporation of a DisplayController and LEDController provides visual feedback and communication capabilities, enhancing human-robot interaction.
- Battery Monitoring: The class also includes a method for battery state monitoring, ensuring the robot operates within its energy constraints.


2. The Camera Class: Enhancing Perception in Robotics

The Camera class is instrumental in augmenting a robot's perception of its surroundings. It leverages the depthai and robothub libraries to manage camera functionalities, which are vital for tasks like navigation, object recognition, and environmental interaction.

- Stream Management: It enables the creation and management of video streams through RobotHub and ROS, crucial for real-time visual data processing.
- Hardware Interface: The class interacts directly with the camera hardware, ensuring optimal utilization of the device's capabilities.
- Flexibility and Control: The inclusion of methods for starting and stopping the camera pipeline, and for publishing video data, provides flexibility and control over the camera operations.

3. The ROS2Manager Class: Streamlining ROS2 Operations

The ROS2Manager class encapsulates the management of ROS2 functionalities. ROS2 (Robot Operating System 2) is an essential component in modern robotics, providing tools for communication between different parts of a robotic system.

- Node Management: This class is responsible for creating and managing nodes in ROS2, facilitating communication between different components of a robot.
- Publisher and Subscriber System: It includes a comprehensive system for creating publishers, subscribers, clients etc. allowing the robot to interact with various data streams efficiently.
- Lifecycle Management: The class also manages the lifecycle of ROS2 processes, including starting and stopping nodes and context, ensuring robust and reliable operations.