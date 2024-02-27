import depthai as dai
import json

from depthai_sdk.components.nn_helper import Path


def create_pipeline(pipeline: dai.Pipeline, config: dict):
    rgb_sensor = create_rgb_sensor(pipeline, fps=config["fps"])
    rgb_input = pipeline.createXLinkIn()
    rgb_input.setStreamName("rgb_input")
    rgb_input.out.link(rgb_sensor.inputControl)
    rgb_mjpeg_encoder = create_mjpeg_encoder(pipeline=pipeline, fps=config["fps"])
    # link
    rgb_sensor.video.link(rgb_mjpeg_encoder.input)
    image_manip = create_image_manip(pipeline=pipeline, source=rgb_sensor.preview, resize=(640, 640))
    detection_nn = create_detecting_nn(pipeline, "nn_models/yolov6n_coco_640x640.blob", source=image_manip.out)
    # output
    create_output(pipeline=pipeline, node=rgb_mjpeg_encoder.bitstream, stream_name="rgb_mjpeg")
    create_output(pipeline=pipeline, node=detection_nn.out, stream_name="detection_nn")


def create_rgb_sensor(pipeline: dai.Pipeline, fps: float) -> dai.node.ColorCamera:
    node = pipeline.createColorCamera()
    node.setBoardSocket(dai.CameraBoardSocket.RGB)
    node.setInterleaved(False)
    node.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
    node.setPreviewNumFramesPool(4)
    node.setPreviewSize(1280, 720)
    node.setVideoSize(1920, 1080)
    node.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
    node.setFps(fps)
    return node


def create_mjpeg_encoder(pipeline: dai.Pipeline, fps: float) -> dai.node.VideoEncoder:
    encoder = pipeline.createVideoEncoder()
    encoder_profile = dai.VideoEncoderProperties.Profile.MJPEG
    encoder.setDefaultProfilePreset(fps, encoder_profile)
    return encoder


def create_image_manip(pipeline: dai.Pipeline, source: dai.Node.Output, resize: tuple[int, int], keep_aspect_ration: bool = False,
                       frame_type: dai.RawImgFrame.Type = dai.RawImgFrame.Type.BGR888p, output_frame_dims: int = 3,
                       blocking_input_queue: bool = False, input_queue_size: int = 4, frames_pool: int = 4,
                       wait_for_config: bool = False) -> dai.node.ImageManip:
    image_manip = pipeline.createImageManip()
    image_manip.setResize(*resize)
    image_manip.setFrameType(frame_type)
    image_manip.setMaxOutputFrameSize(resize[0] * resize[1] * output_frame_dims)
    image_manip.initialConfig.setKeepAspectRatio(keep_aspect_ration)
    image_manip.inputImage.setBlocking(blocking_input_queue)
    image_manip.inputImage.setQueueSize(input_queue_size)
    image_manip.setNumFramesPool(frames_pool)
    image_manip.setWaitForConfigInput(wait_for_config)
    source.link(image_manip.inputImage)
    return image_manip


def create_detecting_nn(pipeline: dai.Pipeline, model: str, source: dai.Node.Output) -> dai.node.NeuralNetwork:
    model_config = Path("nn_models/object_detection_config.json")
    with model_config.open() as f:
        config = json.loads(f.read())
    node = pipeline.createYoloDetectionNetwork()
    nn_metadata = config["nn_config"]["NN_specific_metadata"]
    node.setNumClasses(1)
    node.setCoordinateSize(nn_metadata["coordinates"])
    node.setAnchors(nn_metadata["anchors"])
    node.setAnchorMasks(nn_metadata["anchor_mask"])
    node.setIouThreshold(nn_metadata["iou_threshold"])
    node.input.setBlocking(False)
    blob = dai.OpenVINO.Blob(Path(model).resolve())
    node.setBlob(blob)
    source.link(node.input)
    return node


def create_output(pipeline: dai.Pipeline, node: dai.Node.Output, stream_name: str):
    xout = pipeline.createXLinkOut()
    xout.setStreamName(stream_name)
    node.link(xout.input)
