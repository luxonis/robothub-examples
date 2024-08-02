# P2P Distance Measurement

## Description
This repository contains an application built on top of [DepthAI](https://docs.luxonis.com/software/). This Python script captures depth data from a stereo camera setup and allows the user to click on two points in the captured image to calculate and display the distance between them.

## Prerequisites

- Python 3.x
- OpenCV 
- DepthAI
- NumPy

## Usage
1. Run the python script `app.py` 
2. **Select Points**: Click on the video window to select two points. The distance will be displayed at a line between them.

###### Shortcuts Guide

| Key | Action                           | Description                                                   |
|-----|----------------------------------|---------------------------------------------------------------|
| `q` | Quit                             | Closes the application.                                       |
| `c` | Clear Points                     | Clears all the selected points.                                    |
| `t` | Toggle Tracking                  | Toggles the tracking functionality on or off.       

## Method for Calculating Distance
### Euclidean formula 
$$
\text{distance} = \text{d} = \sqrt{(x_2 - x_1)^2 + (y_2 - y_1)^2 + (z_2 - z_1)^2}
$$

where $x, y, z$ are the coordinates of the two selected points. $z$ is taken from the depth map, coordinates $x$ and $y$ are in pixels and is converted to cm as follows:

$$
\text{cm per px} = f = \frac{2 \cdot z \cdot \tan\left(\frac{\text{HFOV}}{2} \cdot \frac{\pi}{180}\right)}{\text{HPixels}}
$$


## Uncertainty calculation
The only error-prone attribute in the calculation of the distance is the depth value. Since $x$ and $y$ are both calculated (as shown above) from coordinates in pixels and the depth value at the point, the error $\epsilon_{dist}$ can be computed given the depth error rate $\epsilon_z$ (read more about [depth accuracy](https://docs.luxonis.com/hardware/platform/depth/depth-accuracy/)) as follows:

$$
\epsilon_{dist} = \sqrt{\left(\frac{\partial d}{\partial x_1}\epsilon_{x_1}\right)^2 + \left(\frac{\partial d}{\partial y_1}\epsilon_{y_1}\right)^2 + \left(\frac{\partial d}{\partial z_1}\epsilon_{z_1}\right)^2 + \left(\frac{\partial d}{\partial x_2}\epsilon_{x_2}\right)^2 + \left(\frac{\partial d}{\partial y_2}\epsilon_{y_2}\right)^2 + \left(\frac{\partial d}{\partial z_2}\epsilon_{z_2}\right)^2}
$$

---
#### $\epsilon_{x_i}$ and $\epsilon_{y_i}$ \(where $i \in \{1,2\}$\)
The error in $\text{cm per px}$ with respect to $z$ is:

$$
\epsilon_{\text{cm per px}} = \frac{\partial (\text{cm per px})}{\partial z_i} \cdot \epsilon_{z_i} = \frac{2 \cdot \tan\left(\frac{\text{HFOV}}{2} \cdot \frac{\pi}{180}\right)}{\text{HPixels}} \cdot \epsilon_{z_i}
$$

Now we propagate this to get:

$$
\epsilon_{x_i} = x_{px} \cdot \epsilon_{\text{cm per px}} \quad \text{and} \quad \epsilon_{y_i} = y_{px} \cdot \epsilon_{\text{cm per px}}
$$

where $x_{px}, y_{px}$ are the coordinates in pixels, and they have an error rate of 0.

---
#### Partial derivatives
Next step is to derive the partial derivatives in $\epsilon_{dist}$, we obtain:

$$
\frac{\partial d}{\partial x_i} = \frac{x_2-x_1}{d} \quad , \quad \frac{\partial d}{\partial y_i} = \frac{y_2 - y_1}{d} \quad \text{and} \quad \frac{\partial d}{\partial z_i} = \frac{z_2 - z_1}{d}
$$

## Ideas to implement
- add confidence interval
- drag points and multiple measument lines
