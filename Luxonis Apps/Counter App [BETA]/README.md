# Line Crossing Counter Application

This application demonstrates how to perform real-time object detection, tracking, and line crossing counting.
The main objective is to count the number of times a person crosses a predefined line in either direction.

## Requirements

- Luxonis device with an RGB sensor.

## Features

- Real-time object detection using a pre-trained YOLOv6 model.
- Object tracking to maintain identity across frames.
- Line crossing detection to count transitions across a specified line.
- Live visualization of the video stream, object bounding boxes, and line crossing counts.

## Dependencies

- DepthAI SDK
- NumPy
- RobotHub

## Usage

1. Ensure you have the necessary dependencies installed.
2. Update the configuration to match your setup if needed.
3. Run the application.
4. Observe the live view and the line crossing counts as objects move across the line.
