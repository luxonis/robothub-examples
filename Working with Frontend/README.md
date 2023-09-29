# Working with Frontend

This application demonstrates how to process video streams, perform object detection, and send image events to RobotHub
on specific front-end (FE) notifications.

## Requirements

- Luxonis device with an RGB sensor.

## Features

- Real-time object detection using a pre-trained YOLOv6 model.
- Event-driven image sending to RobotHub on receiving 'take picture' notification from FE.
- Live visualization of the video stream.

## Dependencies

- DepthAI SDK
- RobotHub

## Usage

1. Ensure you have the necessary dependencies installed.
2. Update the configuration to match your setup if needed.
3. Run the application.
4. Use 'Send event' button on the front-end to upload image event to RobotHub.
