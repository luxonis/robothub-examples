from robothub_oak.manager import DEVICE_MANAGER
from collections import defaultdict
from depthai_sdk import Visualizer
from robothub_oak.packets import DetectionPacket
import numpy as np
import robothub
import warnings
import time
import json
import cv2

def log_softmax(x):
    e_x = np.exp(x - np.max(x))
    return np.log(e_x / e_x.sum())

class ExampleApplication(robothub.RobotHubApplication):
    def __init__(self):
        super().__init__()

        self.streams = defaultdict(lambda: defaultdict(robothub.StreamHandle))
        self.detections = []
        self.old_detections = []
        
    def on_start(self):
        mask_detections = robothub.CONFIGURATION['mask_detections']
        mask_detections_mode = robothub.CONFIGURATION['mask_detections_mode']
        helmet_detections = robothub.CONFIGURATION['helmet_detections']
        helmet_detections_mode = robothub.CONFIGURATION['helmet_detections_mode']
        vest_detections = robothub.CONFIGURATION['vest_detections']
        vest_detections_mode = robothub.CONFIGURATION['vest_detections_mode']

        print(f"""
Starting with:
Mask detections {"enabled" if mask_detections else "disabled"}, mode {mask_detections_mode}
Helmet detections {"enabled" if helmet_detections else "disabled"}, mode {helmet_detections_mode}
Vest detections {"enabled" if vest_detections else "disabled"}, mode {vest_detections_mode}
""")
        devices = DEVICE_MANAGER.get_all_devices()
        for device in devices:
            color_resolution = '1080p'

            color = device.get_camera('color', resolution=color_resolution, fps=30)
            color.stream_to_hub(name=f'Color stream {device.get_device_name()}', unique_key=f'Color {device.id}')

            if mask_detections:
                face_nn = device.create_neural_network('face-detection-retail-0004', color)

                face_nn.configure(resize_mode='crop')

                mask_nn = device.create_neural_network('sbd_mask_classification_224x224', face_nn)

                mask_nn.add_callback(self.on_mask, output_type='passthrough')

                face_nn.add_callback(self.on_face, output_type='encoded')

                stream_handle = robothub.STREAMS.create_video(device.mxid, f'NN {device.id}', f'Detection stream {device.get_device_name()}')
                self.streams[device.mxid]['NN'] = stream_handle

    def on_mask(self, packet):
        self.old_detections = self.detections
        self.detections = []
        
        for det, rec in zip(packet.detections, packet.nn_data):
            index = np.argmax(log_softmax(rec.getFirstLayerFp16()))
            self.detections.append(index)


    def on_face(self, packet: DetectionPacket):
        vis: Visualizer = packet.visualizer

        try:
            detections = vis.objects[0]
            for i, mask in enumerate(self.detections):
                detections.labels[i] = "Mask" if mask else "No mask"
                detections.colors[i] = (0, 255, 0) if mask else (255, 0, 0)
        except:
            pass
        
        metadata = json.loads(packet.visualizer.serialize())
        timestamp = int(time.time() * 1_000)
        frame_bytes = bytes(packet.msg.getData())
        self.streams[packet.device.mxid]['NN'].publish_video_data(frame_bytes, timestamp, metadata)

        def upload_detection(packet, metadata, tags):
            try:
                frame_bytes = cv2.imencode('.jpg', packet.depthai_sdk_packet.frame)[1].tobytes()

                event = robothub.EVENTS.prepare()
                event.add_frame(frame_bytes, packet.device.mxid, metadata=metadata)
                event.add_tags(tags)
                robothub.EVENTS.upload(event)

            except Exception as e:
                warnings.warn(f'Could not upload detection with error: {e}')

        mode = robothub.CONFIGURATION['mask_detections_mode']
        for old, new in zip(self.old_detections, self.detections):
            if mode == 'not_wearing':
                if old == 1 and new == 0:
                    upload_detection(packet, metadata, ["Mask", "Not wearing"])
            elif mode == 'wearing':
                if old == 0 and new == 1:
                    upload_detection(packet, metadata, ["Mask", "Wearing"])
            elif mode == 'change':
                if old != new:
                    upload_detection(packet, metadata, ["Mask", "Change"])

      
    def start_execution(self):
        DEVICE_MANAGER.start()

    def on_stop(self):
        DEVICE_MANAGER.stop()
