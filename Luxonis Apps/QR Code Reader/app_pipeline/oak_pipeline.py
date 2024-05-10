import depthai as dai
import robothub as rh
from depthai_sdk.components.nn_helper import Path


def create_pipeline(pipeline: dai.Pipeline) -> None:
    fps = 2 if rh.CONFIGURATION["resolution"] == "5312x6000" else 4
    rgb_sensor = create_rgb_sensor(pipeline, fps=fps)
    rgb_input = pipeline.createXLinkIn()
    rgb_input.setStreamName("rgb_input")
    if rh.CONFIGURATION["enable_manual_exposure"]:
        rgb_sensor.initialControl.setManualExposure(rh.CONFIGURATION["manual_exposure"], rh.CONFIGURATION["manual_iso"])
    else:
        rgb_sensor.initialControl.setAutoExposureLimit(rh.CONFIGURATION["exposure_limit"])

    if rh.CONFIGURATION["manual_focus"] != 0:
        rgb_sensor.initialControl.setManualFocus(rh.CONFIGURATION["manual_focus"])

    script_node = create_script_node(pipeline=pipeline, script_name="app_pipeline/script_node.py")
    script_node_qr_crops = create_script_node(pipeline=pipeline, script_name="app_pipeline/script_node_qr_crops.py")
    rgb_sensor.isp.link(script_node.inputs["rgb_frame"])
    rgb_sensor.isp.link(script_node_qr_crops.inputs["rgb_frame"])
    script_node.inputs["rgb_frame"].setBlocking(True)
    script_node_qr_crops.inputs["rgb_frame"].setBlocking(True)
    script_node_qr_crops.inputs["qr_detection_nn"].setBlocking(True)

    image_manip_1to1_crop = create_image_manip(pipeline=pipeline, source=script_node.outputs["image_manip_1to1_crop"], wait_for_config=True,
                                               resize=(rh.CONFIGURATION["high_res_crop_width"], rh.CONFIGURATION["high_res_crop_height"]),
                                               frames_pool=9, frame_type=dai.RawImgFrame.Type.BGR888p, input_queue_size=9, blocking_input_queue=True)
    encoder_crop = (0.029, 0.083, 0.97, 0.9166) if rh.CONFIGURATION["resolution"] == "5312x6000" else (0, 0, 1, 1)
    encoder_manip = create_image_manip(pipeline=pipeline, source=rgb_sensor.isp, wait_for_config=False,
                                       resize=(rh.CONFIGURATION["encoder_frame_width"], rh.CONFIGURATION["encoder_frame_height"]),
                                       crop=encoder_crop,
                                       frames_pool=2, frame_type=dai.RawImgFrame.Type.NV12, input_queue_size=2, blocking_input_queue=False)
    h264_encoder = create_h264_encoder(pipeline=pipeline, fps=4)
    encoder_manip.out.link(h264_encoder.input)
    h264_encoder.setNumFramesPool(2)
    h264_encoder.input.setBlocking(False)
    h264_encoder.input.setQueueSize(2)
    script_node.outputs["image_manip_1to1_crop_cfg"].link(image_manip_1to1_crop.inputConfig)

    nn_input_width = 512
    nn_input_height = 512 if rh.CONFIGURATION["resolution"] == "5312x6000" else 288
    if rh.CONFIGURATION["resolution"] == "5312x6000":
        nn_model_path = "models/qrdet-512x512_openvino_2022.1_3shave.blob"
    elif rh.CONFIGURATION["resolution"] == "4k":
        nn_model_path = "models/qrdet-512x288_openvino_2022.1_5shave.blob"
    elif rh.CONFIGURATION["resolution"] == "1080p":
        nn_model_path = "models/qr_model_512x288_rvc2_openvino_2022.1_6shave.blob"
    else:
        raise ValueError(f"Unknown resolution: {rh.CONFIGURATION['resolution']}")

    image_manip_nn_input_crop = create_image_manip(pipeline=pipeline, source=image_manip_1to1_crop.out,
                                                   resize=(nn_input_width, nn_input_height), frames_pool=9, blocking_input_queue=True,
                                                   input_queue_size=9)

    to_qr_crop_manip = create_image_manip(pipeline=pipeline, source=script_node_qr_crops.outputs["to_qr_crop_manip"],
                                          keep_aspect_ration=False, frame_type=dai.RawImgFrame.Type.BGR888p, blocking_input_queue=True,
                                          input_queue_size=5, wait_for_config=True, max_output_frame_size=5_000_000)
    script_node_qr_crops.outputs["to_qr_crop_manip_cfg"].link(to_qr_crop_manip.inputConfig)

    qr_detection_nn = create_yolo_nn(pipeline=pipeline, source=image_manip_nn_input_crop.out,
                                     model_path=nn_model_path,
                                     confidence_threshold=0.5)
    qr_detection_nn.setNumPoolFrames(10)
    qr_detection_nn.input.setBlocking(True)
    qr_detection_nn.input.setQueueSize(9)

    # script node inputs
    script_node_input = pipeline.createXLinkIn()
    script_node_input.setStreamName("script_node_input")
    script_node_qr_crops_input = pipeline.createXLinkIn()
    script_node_qr_crops_input.setStreamName("script_node_qr_crops_input")
    script_node_input.setNumFrames(1)
    script_node_qr_crops_input.setNumFrames(1)
    script_node_input.setMaxDataSize(8)
    script_node_qr_crops_input.setMaxDataSize(8)

    # linking
    qr_detection_nn.out.link(script_node_qr_crops.inputs["qr_detection_nn"])
    rgb_input.out.link(rgb_sensor.inputControl)
    script_node_input.out.link(script_node.inputs["script_node_input"])
    script_node_qr_crops_input.out.link(script_node_qr_crops.inputs["script_node_qr_crops_input"])

    script_node.inputs["script_node_input"].setQueueSize(1)
    script_node.inputs["script_node_qr_crops_input"].setQueueSize(1)

    # outputs
    create_output(pipeline=pipeline, node=qr_detection_nn.out, stream_name="qr_detection_out")
    create_output(pipeline=pipeline, node=to_qr_crop_manip.out, stream_name="qr_crops")
    create_output(pipeline=pipeline, node=image_manip_1to1_crop.out, stream_name="high_res_frames")
    create_output(pipeline=pipeline, node=h264_encoder.bitstream, stream_name="h264_stream")


def create_rgb_sensor(pipeline: dai.Pipeline, fps: float) -> dai.node.ColorCamera:
    resolution_mapping = {"1080p": dai.ColorCameraProperties.SensorResolution.THE_1080_P,
                          "720p": dai.ColorCameraProperties.SensorResolution.THE_720_P,
                          "4k": dai.ColorCameraProperties.SensorResolution.THE_4_K,
                          "4000x3000": dai.ColorCameraProperties.SensorResolution.THE_4000X3000,
                          "5312x6000": dai.ColorCameraProperties.SensorResolution.THE_5312X6000,
                          "48MP": dai.ColorCameraProperties.SensorResolution.THE_48_MP,
                          }
    node = pipeline.createColorCamera()
    node.setBoardSocket(dai.CameraBoardSocket.RGB)
    node.setInterleaved(False)
    node.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
    node.setNumFramesPool(2, 3, 1, 1, 1)
    node.setResolution(resolution_mapping[rh.CONFIGURATION["resolution"]])
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
    rh_encoder.setNumFramesPool(1)
    return rh_encoder


def create_image_manip(pipeline: dai.Pipeline, source: dai.Node.Output, max_output_frame_size: int = None,
                       resize: tuple[int, int] = None, crop: tuple[float, float, float, float] = None,
                       keep_aspect_ration: bool = False,
                       frame_type: dai.RawImgFrame.Type = dai.RawImgFrame.Type.BGR888p, output_frame_dims: int = 3,
                       blocking_input_queue: bool = False, input_queue_size: int = 4, frames_pool: int = 9,
                       wait_for_config: bool = False) -> dai.node.ImageManip:
    image_manip = pipeline.createImageManip()
    if crop is not None:
        image_manip.initialConfig.setCropRect(crop[0], crop[1], crop[2], crop[3])
    if resize is not None:
        image_manip.setResize(*resize)
        image_manip.setMaxOutputFrameSize(resize[0] * resize[1] * output_frame_dims)
    if max_output_frame_size is not None:
        image_manip.setMaxOutputFrameSize(max_output_frame_size)
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
    nn_yolo.input.setQueueSize(3)
    source.link(nn_yolo.input)
    return nn_yolo


def create_output(pipeline: dai.Pipeline, node: dai.Node.Output, stream_name: str):
    xout = pipeline.createXLinkOut()
    xout.setStreamName(stream_name)
    node.link(xout.input)
