import depthai as dai
import robothub as rh
from depthai_sdk.components.nn_helper import Path


def create_pipeline(pipeline: dai.Pipeline) -> None:
    rgb_sensor = create_rgb_sensor(pipeline, fps=rh.CONFIGURATION["fps"])
    rgb_input = pipeline.createXLinkIn()
    rgb_input.setStreamName("rgb_input")
    if rh.CONFIGURATION["enable_manual_exposure"]:
        rgb_sensor.initialControl.setManualExposure(rh.CONFIGURATION["manual_exposure"], rh.CONFIGURATION["manual_iso"])
    else:
        rgb_sensor.initialControl.setAutoExposureLimit(rh.CONFIGURATION["exposure_limit"])

    if rh.CONFIGURATION["manual_focus"] != 0:
        rgb_sensor.initialControl.setManualFocus(rh.CONFIGURATION["manual_focus"])

    video_encoder = create_h264_encoder(pipeline=pipeline, fps=rh.CONFIGURATION["fps"])
    isp_downsize_manip = create_image_manip(pipeline=pipeline, source=rgb_sensor.isp, resize=(1280, 720), frame_type=dai.RawImgFrame.Type.NV12)
    isp_downsize_manip.out.link(video_encoder.input)

    script_node = create_script_node(pipeline=pipeline, script_name="app_pipeline/script_node.py")

    image_manip_nn_crop = create_image_manip(pipeline=pipeline, source=script_node.outputs["image_manip_nn_crop"],
                                             wait_for_config=True, resize=(1280, 720), frames_pool=20)
    image_manip_nn_crop.inputImage.setBlocking(True)
    script_node.outputs["image_manip_nn_crop_cfg"].link(image_manip_nn_crop.inputConfig)
    script_node.inputs["rgb_frame"].setBlocking(True)

    qr_detection_nn = create_yolo_nn(pipeline=pipeline, source=image_manip_nn_crop.out,
                                     model_path="models/qrdet-n_openvino_2022.1_5shave.blob",
                                     confidence_threshold=0.5)
    qr_detection_nn.setNumPoolFrames(20)

    # linking
    rgb_sensor.preview.link(script_node.inputs["rgb_frame"])
    rgb_input.out.link(rgb_sensor.inputControl)

    # outputs
    create_output(pipeline=pipeline, node=qr_detection_nn.out, stream_name="qr_detection_out")
    create_output(pipeline=pipeline, node=video_encoder.bitstream, stream_name="video_h264_encoded")
    create_output(pipeline=pipeline, node=rgb_sensor.isp, stream_name="rgb_isp_high_res")


def create_rgb_sensor(pipeline: dai.Pipeline, fps: float) -> dai.node.ColorCamera:
    node = pipeline.createColorCamera()
    node.setBoardSocket(dai.CameraBoardSocket.RGB)
    node.setInterleaved(False)
    node.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
    node.setNumFramesPool(2, 2, 5, 1, 5)
    node.setResolution(dai.ColorCameraProperties.SensorResolution.THE_4_K)
    node.setPreviewSize(1280, 720)
    node.setFps(fps)
    return node


def create_script_node(pipeline, script_name: str):
    script_node = pipeline.createScript()
    script_node.setScript(load_script(script_name=script_name))

    return script_node


def load_script(script_name: str):
    from string import Template
    with open(script_name, 'r') as file:
        code = Template(file.read()).substitute(
            DEBUG=''
        )
    return code


def create_h264_encoder(pipeline: dai.Pipeline, fps: float) -> dai.node.VideoEncoder:
    rh_encoder = pipeline.createVideoEncoder()
    rh_encoder_profile = dai.VideoEncoderProperties.Profile.H264_MAIN
    rh_encoder.setDefaultProfilePreset(fps, rh_encoder_profile)
    rh_encoder.input.setQueueSize(2)
    rh_encoder.input.setBlocking(False)
    rh_encoder.setKeyframeFrequency(fps)
    rh_encoder.setRateControlMode(dai.VideoEncoderProperties.RateControlMode.CBR)
    rh_encoder.setNumFramesPool(3)
    return rh_encoder


def create_image_manip(pipeline: dai.Pipeline, source: dai.Node.Output,
                       resize: tuple[int, int],
                       keep_aspect_ration: bool = False,
                       frame_type: dai.RawImgFrame.Type = dai.RawImgFrame.Type.BGR888p, output_frame_dims: int = 3,
                       blocking_input_queue: bool = False, input_queue_size: int = 4, frames_pool: int = 9,
                       wait_for_config: bool = False) -> dai.node.ImageManip:
    image_manip = pipeline.createImageManip()
    image_manip.setResize(*resize)
    image_manip.setMaxOutputFrameSize(resize[0] * resize[1] * output_frame_dims)
    image_manip.initialConfig.setKeepAspectRatio(keep_aspect_ration)

    image_manip.setFrameType(frame_type)

    image_manip.inputImage.setBlocking(blocking_input_queue)
    image_manip.inputImage.setQueueSize(input_queue_size)
    image_manip.setNumFramesPool(frames_pool)
    image_manip.setWaitForConfigInput(wait_for_config)
    source.link(image_manip.inputImage)
    return image_manip


def create_yolo_nn(pipeline: dai.Pipeline, source: dai.Node.Output, model_path: str, confidence_threshold: float) -> dai.node.NeuralNetwork:
    nn_yolo = pipeline.createYoloDetectionNetwork()
    nn_yolo.setBlobPath(Path(model_path))
    nn_yolo.setConfidenceThreshold(confidence_threshold)
    nn_yolo.setNumClasses(1)
    nn_yolo.setCoordinateSize(4)
    nn_yolo.setIouThreshold(0.5)
    nn_yolo.setNumInferenceThreads(2)
    nn_yolo.input.setBlocking(True)  # set blocking, otherwise configs in queue might be overwritten
    nn_yolo.input.setQueueSize(9)
    source.link(nn_yolo.input)
    return nn_yolo


def create_output(pipeline: dai.Pipeline, node: dai.Node.Output, stream_name: str):
    xout = pipeline.createXLinkOut()
    xout.setStreamName(stream_name)
    node.link(xout.input)
