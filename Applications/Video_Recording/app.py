import logging as log
import time

import blobconverter
import depthai as dai
import object_detector_config as nn_config
import robothub as rh
from app_pipeline import host_node
from app_pipeline.oak_pipeline import create_pipeline


class Application(rh.BaseDepthAIApplication):
    video_recording: host_node.VideoRecording
    video_buffer: host_node.VideoBuffer
    image_event: host_node.ImageEvent
    monitor: host_node.Monitor

    def __init__(self):
        super().__init__()

        rh.COMMUNICATOR.on_frontend(
            notification=self.on_fe_notification,
            request=self.on_fe_request,
        )

    def setup_pipeline(self) -> dai.Pipeline:
        """Define the pipeline using DepthAI."""

        log.info(f"App config: {rh.CONFIGURATION}")
        pipeline = dai.Pipeline()
        create_pipeline(pipeline=pipeline)
        return pipeline

    def manage_device(self, device: dai.Device):
        log.info(f"{device.getMxId()} creating output queues...")
        h264_node = host_node.Bridge(device=device, out_name="main_h264", blocking=True)
        mjpeg_node = host_node.Bridge(device=device, out_name="main_mjpeg", blocking=True)
        self.video_recording = host_node.VideoRecording(input_node=h264_node)
        self.video_buffer = host_node.VideoBuffer(input_node=h264_node)
        host_node.VideoEvent(input_node=self.video_buffer)
        host_node.VideoEvent(input_node=self.video_recording)
        self.image_event = host_node.ImageEvent(input_node=mjpeg_node)
        self.monitor = host_node.Monitor(input_node=h264_node)
        log.info(f"{device.getMxId()} Application started")
        host_node.Bridge.run()

    def on_fe_notification(self, session_id, unique_key, payload):
        log.info(f"{payload = } {unique_key=}")
        if unique_key == 'recording_start':
            self.video_recording.switch_on()
            self.monitor.toggle_recording_on()
        elif unique_key == 'recording_stop':
            self.video_recording.switch_off()
            self.monitor.toggle_recording_off()
        elif unique_key == 'send_video_buffer':
            self.video_buffer.send_video()
        elif unique_key == 'send_image_event':
            self.image_event.send_image()

    def on_fe_request(self, session_id, unique_key, payload):
        log.info(f"FE request: {unique_key = }")

    def on_configuration_changed(self, configuration_changes: dict) -> None:
        log.info(f"CONFIGURATION CHANGES: {configuration_changes}")
        if "fps" in configuration_changes:
            log.info(f"FPS change needs a new pipeline. Restarting OAK device...")
            self.restart_device()


def create_rgb_sensor(pipeline: dai.Pipeline,
                      fps: int = 30,
                      resolution: dai.ColorCameraProperties.SensorResolution = dai.ColorCameraProperties.SensorResolution.THE_1080_P,
                      preview_resolution: tuple = (1280, 720),
                      ) -> dai.node.ColorCamera:
    node = pipeline.createColorCamera()
    node.setBoardSocket(dai.CameraBoardSocket.CAM_A)
    node.setInterleaved(False)
    node.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
    node.setPreviewNumFramesPool(4)
    node.setPreviewSize(*preview_resolution)
    node.setVideoSize(1920, 1080)
    node.setResolution(resolution)
    node.setFps(fps)
    return node


def create_h264_encoder(node_input: dai.Node.Output, pipeline: dai.Pipeline, fps: int = 30):
    rh_encoder = pipeline.createVideoEncoder()
    rh_encoder_profile = dai.VideoEncoderProperties.Profile.H264_MAIN
    rh_encoder.setDefaultProfilePreset(fps, rh_encoder_profile)
    rh_encoder.input.setQueueSize(2)
    rh_encoder.input.setBlocking(False)
    rh_encoder.setKeyframeFrequency(fps)
    rh_encoder.setRateControlMode(dai.VideoEncoderProperties.RateControlMode.CBR)
    rh_encoder.setNumFramesPool(3)
    node_input.link(rh_encoder.input)
    return rh_encoder


def create_mjpeg_encoder(node_input: dai.Node.Output, pipeline: dai.Pipeline, fps: int = 30, quality: int = 100):
    encoder = pipeline.createVideoEncoder()
    encoder_profile = dai.VideoEncoderProperties.Profile.MJPEG
    encoder.setDefaultProfilePreset(fps, encoder_profile)
    encoder.setQuality(quality)
    node_input.link(encoder.input)
    return encoder


def create_yolov7tiny_coco_nn(node_input: dai.Node.Output, pipeline: dai.Pipeline) -> dai.node.YoloDetectionNetwork:
    model = "yolov7tiny_coco_640x352"
    node = pipeline.createYoloDetectionNetwork()
    blob = dai.OpenVINO.Blob(blobconverter.from_zoo(name=model, zoo_type="depthai", shaves=6))
    node.setBlob(blob)
    node_input.link(node.input)
    node.input.setBlocking(False)
    # Yolo specific parameters
    node.setConfidenceThreshold(0.5)
    node.setNumClasses(80)
    node.setCoordinateSize(4)
    node.setAnchors([12.0, 16.0, 19.0, 36.0, 40.0, 28.0, 36.0, 75.0, 76.0, 55.0, 72.0, 146.0, 142.0, 110.0, 192.0, 243.0, 459.0, 401.0])
    node.setAnchorMasks({
        "side80": [0, 1, 2],
        "side40": [3, 4, 5],
        "side20": [6, 7, 8]
    })
    node.setIouThreshold(0.5)
    return node


def create_output(pipeline, node_input: dai.Node.Output, stream_name: str):
    xout = pipeline.createXLinkOut()
    xout.setStreamName(stream_name)
    node_input.link(xout.input)


if __name__ == "__main__":
    app = Application()
    app.run()
