import numpy as np

from depthai_sdk import OakCamera
from robothub import LiveView, BaseApplication
from typing import Optional

# List of emotions to be recognized by the neural network
EMOTIONS = ['neutral', 'happy', 'sad', 'surprise', 'anger']

class Application(BaseApplication):
    live_view: Optional[LiveView] = None

    def process_packets(self, packet):
        detections = packet.detections  # detections from face detection model
        nn_data = packet.nnData  # output from second NN

        for detection, recognition in zip(detections, nn_data):
            bbox = [*detection.top_left, *detection.bottom_right]

            emotion_results = np.array(recognition.getFirstLayerFp16())
            # Find the index of the emotion with the highest score
            emotion_name = EMOTIONS[np.argmax(emotion_results)]

            # Visualizations
            self.live_view.add_rectangle(bbox, label=detection.label)
            self.live_view.add_text(emotion_name, coords=(100, 100))

        self.live_view.publish(packet.frame)

    def setup_pipeline(self, oak: OakCamera):
        """
        Define your data pipeline. Can be called multiple times during runtime. Make sure that objects that have to be created only once
        are defined either as static class variables or in the __init__ method of this class.
        """
        color = oak.create_camera(source="color", fps=30, resolution="1080p", encode="h264")
        detection_nn = oak.create_nn(model='face-detection-retail-0004', input=color)
        recognition_nn = oak.create_nn(model='emotions-recognition-retail-0003', input=detection_nn)

        # Create live view, manual_publish indicates that the live view frames will be published manually
        self.live_view = LiveView.create(device=oak, component=color, name="Emotion recognition", manual_publish=True)
        oak.callback(recognition_nn.out.main, self.process_packets)
