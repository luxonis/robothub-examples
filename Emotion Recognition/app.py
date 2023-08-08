import numpy as np
from depthai_sdk import OakCamera

from robothub_oak import LiveView, BaseApplication
from robothub_oak.data_processors import BaseDataProcessor

# List of emotions to be recognized by the neural network
EMOTIONS = ['neutral', 'happy', 'sad', 'surprise', 'anger']


class EmotionRecognition(BaseDataProcessor):
    def __init__(self, live_view: LiveView):
        super().__init__()
        self.live_view = live_view

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


class Application(BaseApplication):
    def setup_pipeline(self, device: OakCamera):
        """This method is the entrypoint for each device and is called upon connection."""
        color = device.create_camera(source="color", fps=30, resolution="1080p", encode="h264")
        detection_nn = device.create_nn(model='face-detection-retail-0004', input=color)
        recognition_nn = device.create_nn(model='emotions-recognition-retail-0003', input=detection_nn)

        live_view = LiveView.create(device=device,
                                    component=detection_nn,
                                    name="Emotion recognition",
                                    manual_publish=True)
        emotion_recognition = EmotionRecognition(live_view=live_view)

        device.callback(recognition_nn.out.main, emotion_recognition)
