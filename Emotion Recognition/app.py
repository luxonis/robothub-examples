import json
import time
from collections import defaultdict

import numpy as np
import robothub
from depthai_sdk import TextPosition
from robothub_oak.manager import DEVICE_MANAGER

# List of emotions to be recognized by the neural network
emotions = ['neutral', 'happy', 'sad', 'surprise', 'anger']


# Define the application class that extends from RobotHubApplication
class Application(robothub.RobotHubApplication):
    streams = defaultdict(lambda: defaultdict(robothub.StreamHandle))

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
            stream_handle = robothub.STREAMS.create_video(device.mxid,
                                                          unique_key=f'nn_{device.get_device_name()}',
                                                          description=f'NN {device.get_device_name()}')
            self.streams[device.mxid]['NN'] = stream_handle

        # Start the device manager
        DEVICE_MANAGER.start()

    def on_emotion(self, packet):
        # Get detections and neural network data from the packet
        detections = packet.detections
        nn_data = packet.nn_data
        visualizer = packet.visualizer

        # Process each record in the neural network data
        for det, rec in zip(detections, nn_data):
            bbox = [*det.top_left, *det.bottom_right]
            # Convert the first layer of the record to a numpy array
            emotion_results = np.array(rec.getFirstLayerFp16())
            # Find the index of the emotion with the highest score
            emotion_name = emotions[np.argmax(emotion_results)]
            # Add the name of the emotion to the visualizer
            visualizer.add_text(emotion_name, bbox=bbox, position=TextPosition.TOP_MID)

        # Configure the visualizer to hide the label - it's automatically added by the RobotHub
        visualizer.detections(hide_label=True)
        visualizer.text(background_transparency=0.0)

        # Serialize the visualizer, load it into a JSON object, and store it in the metadata variable
        metadata = json.loads(visualizer.serialize())

        # Publish the video data to the stream
        encoded_bytes = bytes(packet.depthai_sdk_packet.msg.getData())
        self.streams[packet.device.mxid]['NN'].publish_video_data(encoded_bytes,
                                                                  int(time.perf_counter_ns() / 1_000_000),
                                                                  metadata)

    def start_execution(self):
        # Start the device manager
        DEVICE_MANAGER.start()

    def on_stop(self):
        # Stop the device manager
        DEVICE_MANAGER.stop()
