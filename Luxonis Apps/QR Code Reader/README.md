# QR Code Reader

## Demo

https://github.com/luxonis/robothub-examples/assets/99871801/88e4ae38-d4db-4838-8751-8eb58c74e2de

## Pipeline
![QR_Detector_pipeline](https://github.com/luxonis/robothub-examples/assets/99871801/1325afaf-2ef9-4c16-9e60-c7754dfeeab4)

## Description

The QR Code Reader app is tailored to fully utilize the __IMX582__ sensor (32MP = 5312x6000 pixels) integrated into the __OAK-1 MAX__. For other OAK models,
it should be configured to run at __4K resolution.__

To maximize high resolution capabilities, the QR code detection process functions as follows for the 5312x6000 resolution variant
(the 4K variant follows a similar process with different crop sizes):

1. __Image Cropping:__ The high resolution image is split into nine equally sized crops (1000x1000x3), closely matching the neural input frame size of 512x512.
2. __QR Code Detection:__ Inference is run on each of the cropped sections.
3. __QR Code Cropping:__ For each detected QR code, a crop is made on the high resolution image.
4. __QR Code Decoding:__ The app decodes the QR codes from these crops.
5. __Visualization:__ Locally, results are visualized using OpenCV (cv2), while for LuxonisHub deployment, results are sent as image events.

### Advantages

The QR Code Reader app excels at reading small QR codes that are far away or simply small, or a combination of both. 

In internal tests, the app successfully detected and __decoded a 1.3cm x 1.3cm QR code from 1 meter away__ using the __OAK-1 MAX.__

### Limitations

- __Frame Rate:__ With the 5312x6000 resolution on the OAK-1 MAX, the app runs at a maximum of 2 FPS. 
At 4K resolution, the app achieves around 3.3 FPS, corresponding to neural inference speeds of 18 FPS and 30 FPS, respectively. 
The QR code detection neural network (YOLOv8) used in this app maxes out at 30 FPS.

- __Crop Splitting:__ The app's speed can be increased by reducing the number of crops. 
Splitting the frame into 4 crops allows 7-8 FPS, while splitting it into 2 crops permits up to 15 FPS.

- Live View: Live View is available at 512x512 when running at the 5312x6000 resolution.

- Autofocus: Manual focus is preferable, as autofocus is relatively slow at lower FPS rates.


## Runtime

### Local execution

Run the app locally with:

    python app.py

Ensure all dependencies are installed.

### LuxonisHub Execution

The app is available in LuxonisHub under the __Luxonis Apps__ section as __QR Code Reader__.

## Dependencies

Refer to  `requirements.txt`
