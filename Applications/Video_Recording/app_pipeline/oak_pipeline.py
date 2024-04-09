import json
from pathlib import Path

import depthai as dai
import robothub as rh


def create_pipeline(pipeline: dai.Pipeline):
    rgb_sensor: dai.node.ColorCamera = create_rgb_sensor(pipeline, fps=rh.CONFIGURATION["fps"])
    create_camera_control_queue(pipeline=pipeline, node=rgb_sensor, name="rgb_control")

    if rh.CONFIGURATION["enable_manual_exposure"]:
        rgb_sensor.initialControl.setManualExposure(rh.CONFIGURATION["manual_exposure"], rh.CONFIGURATION["manual_iso"])
    if rh.CONFIGURATION["manual_focus"] > 0:
        rgb_sensor.initialControl.setManualFocus(rh.CONFIGURATION["manual_focus"])

    main_h264_encoder = create_h264_encoder(pipeline=pipeline, fps=rh.CONFIGURATION["fps"], input_node=rgb_sensor.video)
    main_mjpeg_encoder = create_mjpeg_encoder(pipeline=pipeline, fps=rh.CONFIGURATION["fps"], input_node=rgb_sensor.video)

    # properties
    if rh.CONFIGURATION["flip_camera"]:
        rgb_sensor.setImageOrientation(dai.CameraImageOrientation.ROTATE_180_DEG)

    # controls
    main_input = pipeline.createXLinkIn()
    main_input.setStreamName("main_input")

    # outputs
    create_output(pipeline=pipeline, node=main_h264_encoder.bitstream, stream_name="main_h264")
    create_output(pipeline=pipeline, node=main_mjpeg_encoder.bitstream, stream_name="main_mjpeg")


def create_rgb_sensor(pipeline: dai.Pipeline, fps: float) -> dai.node.ColorCamera:
    node = pipeline.createColorCamera()
    node.setBoardSocket(dai.CameraBoardSocket.RGB)
    node.setInterleaved(False)
    # node.setVideoSize(1920, 1080)
    resolution_mapping = {"1080p": dai.ColorCameraProperties.SensorResolution.THE_1080_P,
                          "720p": dai.ColorCameraProperties.SensorResolution.THE_720_P,
                          "4k": dai.ColorCameraProperties.SensorResolution.THE_4_K
                          }
    resolution = resolution_mapping[rh.CONFIGURATION["resolution"]]
    node.setResolution(resolution)
    node.setFps(fps)
    return node


def create_output(pipeline, node: dai.Node.Output, stream_name: str):
    xout = pipeline.createXLinkOut()
    xout.setStreamName(stream_name)
    node.link(xout.input)


def create_h264_encoder(pipeline: dai.Pipeline, fps, input_node: dai.Node.Output):
    rh_encoder = pipeline.createVideoEncoder()
    rh_encoder_profile = dai.VideoEncoderProperties.Profile.H264_MAIN
    rh_encoder.setDefaultProfilePreset(fps, rh_encoder_profile)
    rh_encoder.input.setQueueSize(2)
    rh_encoder.input.setBlocking(False)
    rh_encoder.setKeyframeFrequency(fps)
    rh_encoder.setRateControlMode(dai.VideoEncoderProperties.RateControlMode.CBR)
    rh_encoder.setNumFramesPool(3)
    input_node.link(rh_encoder.input)
    return rh_encoder


def create_mjpeg_encoder(pipeline: dai.Pipeline, fps: int, input_node: dai.Node.Output):
    encoder = pipeline.createVideoEncoder()
    encoder_profile = dai.VideoEncoderProperties.Profile.MJPEG
    encoder.setDefaultProfilePreset(fps, encoder_profile)
    input_node.link(encoder.input)
    return encoder


def create_camera_control_queue(pipeline: dai.Pipeline, node, name: str):
    cam_control = pipeline.createXLinkIn()
    cam_control.setMaxDataSize(1)
    cam_control.setNumFrames(1)
    cam_control.setStreamName(name)
    cam_control.out.link(node.inputControl)


if __name__ == "__main__":
    _pipeline = dai.Pipeline()
    create_pipeline(_pipeline)
    with dai.Device(_pipeline) as device:
        device.startPipeline()
