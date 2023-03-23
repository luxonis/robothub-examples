## Person detection

This App sends people detections to Robothub.
Sends current frame if a person is detected and waits 10 seconds before sending another detection.

### Requirements 
- An "OAK-D type" device - e.g. OAK-D, OAK-D-Pro, OAK-D-S2, OAK-D-Poe or similar. OAK-FFC-nP type device can also work if a color sensor is inserted into slot A and a mono-pair is inserted into slots B and C.

### Usage 
- Assign a single OAK-D type device to the App and run it, it will send pictures of detected people to the Robothub detections.
- Neural network threshold for detection can be set in configuration.