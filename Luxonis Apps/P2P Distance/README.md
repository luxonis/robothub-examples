# P2P Distance Measurement

## Description
This repository contains an application built on top of [DepthAI](https://docs.luxonis.com/software/). This Python script captures depth data from a stereo camera setup and allows the user to click on two points in the captured image to calculate and display the distance between them.

## Prerequisites

- Python 3.x
- OpenCV 
- DepthAI
- NumPy

## Usage
1. Run the python script `app_poc.py` 
2. **Select Points**: Click on the video window to select two points. The distance will be displayed at a line between them. Press 'c' to clear points or simply click to the next point to create new measurement.
3. Press 'q' to exit.

## Method for Calculating Distance
### Euclidean formula 
$$
\text{distance} = \sqrt{(x_2 - x_1)^2 + (y_2 - y_1)^2 + (z_2 - z_1)^2}
$$

where $x, y, z$ are the coordinates of the two selected points. $z$ is taken from the depth map, coordinates $x$ and $y$ are in pixels and is converted to cm as follows:

$$
\text{cm per px} = \frac{2 \cdot z \cdot \tan\left(\frac{\text{HFOV}}{2} \cdot \frac{\pi}{180}\right)}{\text{HPixels}}
$$

## Ideas to implement
- pinned points
- add confidence interval
- drag points and multiple measument lines
