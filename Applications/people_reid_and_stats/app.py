import depthai as dai
import logging as log
import time

from depthai_sdk import OakCamera
from face_features import FaceFeatures
from line_counter import LineCounter
from monitor_robothub import Monitor

from people_faces_sync import PeopleFacesSync
from people_tracking import PeopleTracking
from people_tracking_sync import PeopleTrackingSync
from pipeline_robothub import create_pipeline
from recorder import Recorder
from robothub import BaseDepthAIApplication


class CounterApp(BaseDepthAIApplication):

    def __init__(self):
        # App
        super().__init__()
        self.oak: OakCamera = None

    def setup_pipeline(self) -> dai.Pipeline:
        log.info(f"CONFIGURATION: {self.config}")
        pipeline = dai.Pipeline()
        create_pipeline(pipeline=pipeline, config=self.config)
        return pipeline

    def manage_device(self, device: dai.Device):
        log.info(f"DepthAI version: {dai.__version__}")
        log.info(f"Oak started. getting queues...")
        rgb_preview = device.getOutputQueue(name="rgb_preview", maxSize=5, blocking=False)
        rgb_mjpeg = device.getOutputQueue(name="rgb_mjpeg", maxSize=5, blocking=False)
        object_detections = device.getOutputQueue(name="object_detection_nn", maxSize=5, blocking=False)
        face_detections = device.getOutputQueue(name="face_detection_nn", maxSize=5, blocking=False)
        emotion_detections = device.getOutputQueue(name="emotion_detection_nn", maxSize=20, blocking=False)
        age_gender_detections = device.getOutputQueue(name="age_gender_detection_nn", maxSize=20, blocking=False)
        re_id = None
        tracker = device.getOutputQueue(name="object_tracker", maxSize=5, blocking=False)
        # host nodes
        face_features = FaceFeatures(age_gender_queue=age_gender_detections, emotions_queue=emotion_detections)
        people_tracking_sync = PeopleTrackingSync()
        people_tracking = PeopleTracking(input_node=people_tracking_sync, re_id_queue=re_id)
        line_counter = LineCounter(source_node=people_tracking_sync)
        people_faces_sync = PeopleFacesSync(people_tracking=people_tracking, face_features=face_features)
        #
        monitor = Monitor(input_node=people_faces_sync)
        video_recorder = Recorder(input_node=people_faces_sync)

        log.info(f"Polling starting...")
        while self.running:
            if rgb_preview.has():
                rgb_frame: dai.ImgFrame = rgb_preview.get()
                people_tracking_sync.rgb_frame_callback(rgb_frame=rgb_frame)
            if rgb_mjpeg.has():
                rgb_mjpeg_frame: dai.ImgFrame = rgb_mjpeg.get()
                people_tracking_sync.rgb_mjpeg_frame_callback(rgb_mjpeg_frame=rgb_mjpeg_frame)
            if object_detections.has():
                object_detections_frame: dai.ImgDetections = object_detections.get()
                people_tracking_sync.people_detections_callback(people_detections_frame=object_detections_frame)
            if tracker.has():
                tracker_frame = tracker.get()
                people_tracking_sync.object_tracker_callback(object_tracker_frame=tracker_frame)
            if face_detections.has():
                face_detections_frame: dai.ImgDetections = face_detections.get()
                face_features.face_features_callback(face_detections_frame=face_detections_frame)
                log.debug(f"Faces ID: {face_detections_frame.getSequenceNum()}")
            time.sleep(0.01)

    def start_execution(self):
        while self.running:
            time.sleep(0.5)

    def on_configuration_changed(self, configuration_changes: dict) -> None:
        log.info(f"CONFIGURATION CHANGES: {configuration_changes=} {self.config=}")
