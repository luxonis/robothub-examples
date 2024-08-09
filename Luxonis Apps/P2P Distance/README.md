# P2P Distance Measurement

## Description
This repository contains an application built on top of [DepthAI](https://docs.luxonis.com/software/). This Python script captures depth data from a stereo camera setup and allows the user to click on two points in the captured image to calculate and display the distance between them.

## Prerequisites

- Python 3.x
- OpenCV 
- DepthAI
- NumPy

## Usage
1. **Run the application**: Start the application by running the Python script `app.py` in your terminal.
    ```bash
    python app.py
    ```

2. **Select Points**: Click on the video window to select two points. The distance between these points will be calculated and displayed with a line connecting them.

3. **Interact with the application** using keyboard shortcuts:

### Shortcuts Guide

| Key | Action                           | Description                                                   |
|-----|----------------------------------|---------------------------------------------------------------|
| `q` | Quit                             | Closes the application.                                       |
| `c` | Clear Points                     | Clears all the selected points.                               |
| `i` | Toggle Confidence Interval       | Toggles the display of the confidence interval for distance.  |
| `1` | Switch to Tracking Mode          | Enables tracking for both selected points.                    |
| `2` | Switch to Meter Mode             | Enables tracking for only one selected point.                 |
| `3` | Switch to Static Mode            | Disables point tracking.                                      |


###### Confidence interval
The standard deviation is time-based, since the distance is not static (due to depth value not being static), this feature collect the last 50 distance values and shows you the average plus a confidence interval. 

>Showing the confidence interval is always disabled when tracking is off (since it only make sense when we are measuring the distance between same points in the space).

###### Zero Depth Mask Trackbar
Dragging this shows pixels where depth value is unknown in red.

## Distance Calculation Using Camera Intrinsic Matrix (K Matrix)

### Overview

The `DistanceCalculator` class includes a method for calculating the 3D Euclidean distance between two points using the camera's intrinsic matrix, also known as the **K matrix**.

### What is the K Matrix 

The K matrix, or intrinsic matrix, is a 3x3 matrix that contains the camera's internal parameters, including focal length and the optical center. It's essential for mapping 3D world coordinates to 2D image coordinates and vice versa. The K matrix is defined as:

$$
K = \begin{bmatrix}
f_x & 0 & c_x \\
0 & f_y & c_y \\
0 & 0 & 1
\end{bmatrix}
$$

- $f_x$  and  $f_y$  are the focal lengths in the x and y directions.
- $c_x$  and  $c_y$  are the coordinates of the principal point (optical center).

### Why the K Matrix?

Calculating distance using the K matrix is more effective and precise, especially when dealing with real-world camera systems. By incorporating the K matrix, the method takes into account the specific properties of the camera, which can vary between camera models and setups. 

### Calculation Details

Given the homogenous vectors in the 2D camera coordinates system $\vec{u} = \begin{bmatrix} x_1 \\ y_1 \\ 1 \end{bmatrix}$ and depth value $z$ (in some distance unit, ex. cm). In our application, the $z$ value comes from [Stereo Node](https://docs.luxonis.com/software/depthai-components/nodes/stereo_depth). We can obtain the vector $\vec{p}$ in the 3D world:

$$
\vec{p}=K^{-1} \cdot \vec{u} \cdot z
$$

## Ideas to implement
- drag points and multiple measument lines
