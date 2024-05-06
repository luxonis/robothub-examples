# QR Code Reader

## Demo

https://github.com/luxonis/robothub-examples/assets/99871801/88e4ae38-d4db-4838-8751-8eb58c74e2de

## Pipeline
![QR_Detector_pipeline](https://github.com/luxonis/robothub-examples/assets/99871801/1325afaf-2ef9-4c16-9e60-c7754dfeeab4)

## Description

The QR Code Reader app is specifically designed to take full advantage of the __IMX582__ sensor. It is integrated into the OAK-1 MAX where it
runs at 32MP mode (5312x6000 pixels). On other OAKs it needs to be setup to run with the 4k resolution.

To take the full advantage of high resolutions, the QR code detection part works like this (The 5312x6000 resolution variant. The 4k variant is very similar, mainly the crop sizes are different.):

1. Split the high resolution image into nine equally sized crops (1000x1000x3). The goal here is to get as close as possible to the neural input frame size, which is 512x512.
2. Run QR code detection inference on each of them
3. Take the QR code detection results and for each detected QR code make a QR code crop on the high resolution image
4. In the app, run QR code decoding on the QR code crops
5. When running locally, visualize results using cv2. When running as a LuxonisHub app, send results as image events to LuxonisHub

### Advantages

The QR code Reader app can read QR codes which appear very small in the frame. This means the QR code is either far away, or 
it is small, or some combination of the two. The app achieves this by.

In our internal testing, we were able to correctly detect and decode a 1,3cm x 1,3cm QR code which was 1m away from the OAK-1 MAX. 

### Limitations

Every frame is split into 9 smaller frames and each of them is fed into QR code detection neural network. When running this app on the __5312x6000 on the OAK-1 MAX,__
this allows maximum of 2FPS. When 4k resolution is used, the app can run at around 3.3 FPS. For the neural network this means
it runs inference at 18FPS and 30FPS.

The limit inference speed for the QR code detection neural network (YOLO8) used in this app is around 30FPS.
The way to make the QR code detection faster, the high resolution frame would have to be split into fewer
crops. Splitting the frame into 4 crops would allow the app run at 7-8 FPS, splitting it into 2 crops would allow for 15FPS etc...

There is no LiveView when running as a LuxonisHub app. Run the app locally to see a live video feed.

It is usually better to use manual focus, otherwise the autofocus is relatively slow because of the low overall FPS rate


## Runtime

You can run this app locally:

    python app.py

make sure to install all dependencies

You can run this app in LuxonisHub. It is available in the __Luxonis Apps__ section under the name __QR Code Reader__

## Dependencies

see `requirements.txt`
