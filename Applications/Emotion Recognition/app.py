import numpy as np
from depthai_sdk import OakCamera
from robothub import LiveView, BaseApplication

# List of emotions to be recognized by the neural network
EMOTIONS = ['neutral', 'happy', 'sad', 'surprise', 'anger']


class EmotionRecognition:
    def __init__(self, live_view):
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
    def setup_pipeline(self, oak: OakCamera):
        """
        This method is the entrypoint for the device and is called upon connection.
        Note: This method can be called multiple times if the device is disconnected and reconnected.
        """
        color = oak.create_camera(source="color", fps=30, resolution="1080p", encode="h264")
        detection_nn = oak.create_nn(model='face-detection-retail-0004', input=color)
        recognition_nn = oak.create_nn(model='emotions-recognition-retail-0003', input=detection_nn)

        # Create live view, manual_publish indicates that the live view frames will be published manually
        live_view = LiveView.create(device=oak,
                                    component=color,
                                    name="Emotion recognition",
                                    manual_publish=True)

        # Set live view for emotion recognition processor, so it can publish frames
        emotion_recognition_processor = EmotionRecognition(live_view)
        oak.callback(recognition_nn.out.main, emotion_recognition_processor.process_packets)
