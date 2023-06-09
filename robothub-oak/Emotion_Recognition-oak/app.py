import robothub
from robothub_oak.manager import DEVICE_MANAGER
import cv2
import numpy as np
from collections import defaultdict
import time
import json
from depthai_sdk import OakCamera, TextPosition

# List of emotions to be recognized by the neural network
emotions = ['neutral', 'happy', 'sad', 'surprise', 'anger']

# Define the application class that extends from RobotHubApplication
class Application(robothub.RobotHubApplication):
    def __init__(self):
        # Initialize the superclass
        super().__init__()
        # Create a defaultdict to handle streams for each device
        self.streams = defaultdict(lambda: defaultdict(robothub.StreamHandle))

    def on_start(self):
        # Get all connected devices
        devices = DEVICE_MANAGER.get_all_devices()

        # For each device, perform the following operations
        for device in devices:
            # Get the color camera feed from the device
            color = device.get_camera('color', resolution='1080p', fps=30)      
            # Create a face-detection neural network with the color camera feed as input
            face_nn = device.create_neural_network('face-detection-retail-0004', color)
            # Configure the face detection network to resize by cropping
            face_nn.configure(resize_mode='crop')
            # Create an emotion-recognition neural network with the face detection network as input
            emotion_nn = device.create_neural_network('emotions-recognition-retail-0003', face_nn)
            # Add a callback to the emotion recognition network
            emotion_nn.add_callback(self.on_emotion)
            # Create a video stream for the device and save it in the streams dictionary
            stream_handle = robothub.STREAMS.create_video(device.mxid, f'NN {device.get_device_name()}', f'NN {device.get_device_name()}')
            self.streams[device.mxid]['NN'] = stream_handle

        # Start the device manager
        DEVICE_MANAGER.start()

    def on_emotion(self, packet):
        # Get detections and neural network data from the packet
        detections = packet.detections
        nn_data = packet.nn_data

        # Process each record in the neural network data
        for rec in nn_data:
            # Convert the first layer of the record to a numpy array
            emotion_results = np.array(rec.getFirstLayerFp16())
            # Find the index of the emotion with the highest score
            emotion_name = emotions[np.argmax(emotion_results)]
            # Reset the visualizer
            packet.visualizer.reset()
            # Add a bounding box to the visualizer
            packet.visualizer.add_bbox(bbox, color=None, thickness=None, bbox_style=None, label=None)
            # Add the name of the emotion to the visualizer
            packet.visualizer.add_text(emotion_name, position=TextPosition.BOTTOM_RIGHT)
            
        # Serialize the visualizer, load it into a JSON object, and store it in the metadata variable
        metadata = json.loads(packet.visualizer.serialize())
        
        # Publish the video data to the stream
        self.streams[packet.device.mxid]['NN'].publish_video_data(bytes(bytes(packet.depthai_sdk_packet.msg.getData())), int(time.perf_counter() * 1000), metadata)

    def on_stop(self):
        # Stop the device manager
        DEVICE_MANAGER.stop()
