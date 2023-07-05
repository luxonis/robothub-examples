## YouTube streaming application with people detection

This application streams video from Luxonis cameras to YouTube, detecting objects in the image in the process. The YOLO model is used for detection.

### Requirements 

- An OAK device with an RGB sensor is required. Devices such as OAK-D, OAK-D-Lite, OAK-D-Pro or OAK-FFC-4P equipped with an RGB sensor will do.
- You need to register in Youtube Studio and get a stream key.

### Usage

1. After installing the App, go into the "Configuration" tab in RobotHub and add your stream key. 
2. Optionally you can also change the stream FPS and bitrate here. 
3. Upon pressing "Save Changes", the app will restart itself and start streaming to YouTube.