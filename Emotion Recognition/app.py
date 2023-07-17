import numpy as np
from depthai_sdk import OakCamera

from robothub_oak import LiveView
from robothub_oak.application import RobotHubApplication
from robothub_oak.data_processors import BaseDataProcessor

# List of emotions to be recognized by the neural network
EMOTIONS = ['neutral', 'happy', 'sad', 'surprise', 'anger']


class EmotionRecognition(BaseDataProcessor):
    def process_packets(self, packet):
        detections = packet.detections  # detections from face detection model
        nn_data = packet.nnData  # output from second NN

        live_view = LiveView.get(unique_key='emotion_stream')
        for detection, recognition in zip(detections, nn_data):
            bbox = [*detection.top_left, *detection.bottom_right]

            emotion_results = np.array(recognition.getFirstLayerFp16())
            # Find the index of the emotion with the highest score
            emotion_name = EMOTIONS[np.argmax(emotion_results)]

            # Visualizations
            live_view.add_bbox(bbox=bbox, label=detection.label)
            live_view.add_text(emotion_name, coords=(100, 100))

        live_view.publish(packet.frame)


class ExampleApplication(RobotHubApplication):
    def __init__(self):
        super().__init__()
        self.emotion_recognition = EmotionRecognition()

    def setup_pipeline(self, device: OakCamera):
        """This method is the entrypoint for each device and is called upon connection."""
        color = device.create_camera(source="color", fps=30, resolution="1080p", encode="h264")
        detection_nn = device.create_nn(model='face-detection-retail-0004', input=color)
        recognition_nn = device.create_nn(model='emotions-recognition-retail-0003', input=detection_nn)

        LiveView.create(device=device, component=detection_nn, title="Emotion recognition",
                        unique_key=f"emotion_stream", manual_publish=True)

        device.callback(recognition_nn.out.main, self.emotion_recognition)
