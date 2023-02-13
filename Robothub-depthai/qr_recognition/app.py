import blobconverter
import cv2
import numpy as np
from depthai_sdk import AspectRatioResizeMode
from depthai_sdk.oak_outputs.normalize_bb import NormalizeBoundingBox

import robothub_depthai


def expand_detection(det, percent=2):
    percent /= 100
    det.xmin = np.clip(det.xmin - percent, 0, 1)
    det.ymin = np.clip(det.ymin - percent, 0, 1)
    det.xmax = np.clip(det.xmax + percent, 0, 1)
    det.ymax = np.clip(det.ymax + percent, 0, 1)


class Application(robothub_depthai.RobotHubApplication):
    def __init__(self):
        super().__init__()
        self.detector = cv2.QRCodeDetector()

    def callback(self, packet):
        for i, detection in enumerate(packet.img_detections.detections):
            expand_detection(detection)
            bbox = detection.xmin, detection.ymin, detection.xmax, detection.ymax
            bbox = NormalizeBoundingBox((384, 384), AspectRatioResizeMode.LETTERBOX).normalize(packet.frame, bbox)

            cropped_qr = packet.frame[bbox[1]:bbox[3], bbox[0]:bbox[2]]

            data, _, _ = self.detector.detectAndDecode(cropped_qr)
            if data:
                print(f'Detected QR: {data}')

    def on_start(self):
        for camera in self.unbooted_cameras:
            color = camera.create_camera('color', resolution='1080p', fps=30)

            nn_path = blobconverter.from_zoo(name='qr_code_detection_384x384', zoo_type='depthai', shaves=6)
            nn = camera.create_nn(nn_path, color, nn_type='mobilenet')

            # It will automatically create a stream and assign matching callback based on Component type
            camera.create_stream(component=nn,
                                 unique_key=f'nn_stream_{camera.id}',
                                 name=f'Detections stream {camera.id}')
            camera.callback(nn, callback=self.callback)
