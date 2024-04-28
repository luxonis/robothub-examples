import logging as log

import depthai as dai
import robothub as rh


def create_pipeline(pipeline: dai.Pipeline):
    rgb_sensor: dai.node.ColorCamera = create_rgb_sensor(pipeline, fps=rh.CONFIGURATION["fps"])
    # because of potentially high RAM consumption
    # https://docs.luxonis.com/projects/hardware/en/latest/pages/articles/sensors/imx582/
    rgb_sensor.setNumFramesPool(2, 2, 1, 1, 1)
    create_camera_control_queue(pipeline=pipeline, node=rgb_sensor, name="rgb_control")

    if rh.CONFIGURATION["enable_manual_exposure"]:
        rgb_sensor.initialControl.setManualExposure(rh.CONFIGURATION["manual_exposure"], rh.CONFIGURATION["manual_iso"])
    if rh.CONFIGURATION["manual_focus"] > 0:
        rgb_sensor.initialControl.setManualFocus(rh.CONFIGURATION["manual_focus"])

    video_h264_encoder = create_h264_encoder(pipeline=pipeline, fps=rh.CONFIGURATION["fps"], input_node=rgb_sensor.video)
    video_h264_encoder.setNumFramesPool(1)

    # outputs
    if rh.CONFIGURATION["enable_jpeg_encoding_images"]:
        log.info(f"Enabling JPEG encoding of images")
        still_mjpeg_encoder = create_mjpeg_encoder(pipeline=pipeline, fps=rh.CONFIGURATION["fps"], input_node=rgb_sensor.still)
        still_mjpeg_encoder.setNumFramesPool(1)
        create_output(pipeline=pipeline, node=still_mjpeg_encoder.bitstream, stream_name="still")
    else:
        log.info(f"Disabling JPEG encoding of images")
        create_output(pipeline=pipeline, node=rgb_sensor.still, stream_name="still")

    create_output(pipeline=pipeline, node=video_h264_encoder.bitstream, stream_name="video_h264")

    # properties
    if rh.CONFIGURATION["flip_camera"]:
        rgb_sensor.setImageOrientation(dai.CameraImageOrientation.ROTATE_180_DEG)


def create_rgb_sensor(pipeline: dai.Pipeline, fps: float) -> dai.node.ColorCamera:
    node = pipeline.createColorCamera()
    node.setBoardSocket(dai.CameraBoardSocket.RGB)
    node.setInterleaved(False)
    image_resolution_mapping = {"1080p": dai.ColorCameraProperties.SensorResolution.THE_1080_P,
                                "720p": dai.ColorCameraProperties.SensorResolution.THE_720_P,
                                "4k": dai.ColorCameraProperties.SensorResolution.THE_4_K,
                                "4000x3000": dai.ColorCameraProperties.SensorResolution.THE_4000X3000,
                                "5312x6000": dai.ColorCameraProperties.SensorResolution.THE_5312X6000,
                                "48MP": dai.ColorCameraProperties.SensorResolution.THE_48_MP,
                                }
    video_resolution_mapping = {"1080p": (1920, 1080),
                                "720p": (1280, 720),
                                "4k": (3840, 2160),
                                "4000x3000": (4000, 3000),
                                "5312x6000": (5312, 6000),
                                }
    image_resolution = image_resolution_mapping[rh.CONFIGURATION["image_resolution"]]
    video_resolution = video_resolution_mapping[rh.CONFIGURATION["video_resolution"]]
    node.setResolution(image_resolution)
    node.setVideoSize(*video_resolution)
    if image_resolution == "5312x6000" or image_resolution == "48MP":
        log.info(f"Setting fps to 10 because image resolution is 5312x6000 or 48MP")
        fps = 3
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
    cam_control.setMaxDataSize(2)
    cam_control.setNumFrames(2)
    cam_control.setStreamName(name)
    cam_control.out.link(node.inputControl)


if __name__ == "__main__":
    _pipeline = dai.Pipeline()
    create_pipeline(_pipeline)
    with dai.Device(_pipeline) as device:
        device.startPipeline()
