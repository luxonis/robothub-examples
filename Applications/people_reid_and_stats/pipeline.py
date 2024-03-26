import blobconverter
import depthai as dai
import json

from depthai_sdk.components.nn_helper import Path
from robothub import CONFIGURATION
from string import Template


def create_script(fps: int, path: Path):
    with open(path, 'r') as file:
        code = Template(file.read()).substitute(
            FPS=f"{fps}"
        )
        return code


def create_pipeline(pipeline: dai.Pipeline, config: dict):
    rgb_sensor = create_rgb_sensor(pipeline, fps=config["fps"])
    rgb_input = pipeline.createXLinkIn()
    rgb_input.setStreamName("rgb_input")
    rgb_input.out.link(rgb_sensor.inputControl)
    rgb_h264_encoder = create_h264_encoder(pipeline=pipeline, fps=config["fps"])
    rgb_mjpeg_encoder = create_mjpeg_encoder(pipeline=pipeline, fps=config["fps"])
    # link
    rgb_sensor.video.link(rgb_h264_encoder.input)
    rgb_sensor.video.link(rgb_mjpeg_encoder.input)
    # rgb_sensor.initialControl.setManualFocus(100)
    image_manip = create_image_manip(pipeline=pipeline, source=rgb_sensor.preview, resize=(640, 640))
    # config_sensor(rgb_sensor)
    object_detection_nn = create_object_detecting_nn(pipeline, "nn_models/yolov6n_coco_640x640", source=image_manip.out)
    object_tracker = create_object_tracker(pipeline, image_source=object_detection_nn.passthrough, detections_source=object_detection_nn.out)

    script_node = pipeline.createScript()
    script_node.setScript(create_script(fps=config["fps"], path=Path("script_node.py")))

    # for re-id
    # script_node_people = pipeline.createScript()
    # script_node_people.setScript(create_script(fps=config["fps"], path=Path("script_node_people.py")))

    # face detection nn
    image_manip_face_det = create_image_manip(pipeline=pipeline, source=script_node.outputs["manip_face_img"], resize=(300, 300))
    face_detection_nn, face_det_nn_input_size = create_face_detection_nn(pipeline=pipeline, source=image_manip_face_det.out)

    # emotion detection nn
    image_manip_emotions = create_image_manip(pipeline=pipeline, source=script_node.outputs["manip_emotions_img"], resize=(64, 64),
                                              blocking_input_queue=True, input_queue_size=20, frames_pool=20, wait_for_config=True)
    emotion_detection_nn = create_emotion_detection_nn(pipeline=pipeline, source=image_manip_emotions.out)

    # age gender recognition nn
    image_manip_age_gender = create_image_manip(pipeline=pipeline, source=script_node.outputs["manip_age_gender_img"], resize=(62, 62),
                                                blocking_input_queue=True, input_queue_size=20, frames_pool=20, wait_for_config=True)
    age_gender_nn = create_age_gender_nn(pipeline=pipeline, source=image_manip_age_gender.out)

    # RE-ID nn - app was too slow, maybe it is possible to make it work so just keeping the code here in case anyone wants to try
    # re-id nn
    # image_manip_re_id = create_image_manip(pipeline=pipeline, source=script_node_people.outputs["manip_reid_img"], resize=(128, 256),
    #                                        blocking_input_queue=True, input_queue_size=20, frames_pool=20, wait_for_config=True)
    # re_id_nn = create_re_id_nn(pipeline=pipeline, source=image_manip_re_id.out)

    # script node IO
    rgb_sensor.preview.link(script_node.inputs["rgb_frames"])
    # for re-id
    # rgb_sensor.preview.link(script_node_people.inputs["rgb_frames"])
    # object_tracker.out.link(script_node_people.inputs["people_tracker"])
    face_detection_nn.out.link(script_node.inputs["face_detections"])
    script_node.outputs["manip_emotions_cfg"].link(image_manip_emotions.inputConfig)
    script_node.outputs["manip_age_gender_cfg"].link(image_manip_age_gender.inputConfig)
    # script_node_people.outputs["manip_reid_cfg"].link(image_manip_re_id.inputConfig)

    # outputs
    create_output(pipeline=pipeline, node=rgb_h264_encoder.bitstream, stream_name="rgb_preview")
    create_output(pipeline=pipeline, node=rgb_mjpeg_encoder.bitstream, stream_name="rgb_mjpeg")
    create_output(pipeline=pipeline, node=object_detection_nn.out, stream_name="object_detection_nn")
    create_output(pipeline=pipeline, node=object_tracker.out, stream_name="object_tracker")
    create_output(pipeline=pipeline, node=face_detection_nn.out, stream_name="face_detection_nn")
    create_output(pipeline=pipeline, node=emotion_detection_nn.out, stream_name="emotion_detection_nn")
    create_output(pipeline=pipeline, node=age_gender_nn.out, stream_name="age_gender_detection_nn")
    # create_output(pipeline=pipeline, node=re_id_nn.out, stream_name="re_id_nn")


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


def create_object_detecting_nn(pipeline: dai.Pipeline, model: str, source: dai.Node.Output) -> dai.node.NeuralNetwork:
    model_config = Path("nn_models/object_detection_config.json")
    with model_config.open() as f:
        config = json.loads(f.read())
    node = pipeline.createYoloDetectionNetwork()
    nn_metadata = config["nn_config"]["NN_specific_metadata"]
    # node.setNumClasses(nn_metadata["classes"])
    node.setNumClasses(1)
    node.setCoordinateSize(nn_metadata["coordinates"])
    node.setAnchors(nn_metadata["anchors"])
    node.setAnchorMasks(nn_metadata["anchor_masks"])
    node.setIouThreshold(nn_metadata["iou_threshold"])
    node.setConfidenceThreshold(CONFIGURATION["confidence_threshold"])
    node.input.setBlocking(False)
    blob = dai.OpenVINO.Blob(Path("nn_models/yolov6n_coco_640x640.blob").resolve())
    node.setBlob(blob)
    source.link(node.input)
    return node


def create_face_detection_nn(pipeline: dai.Pipeline, source: dai.Node.Output) -> tuple[dai.node.MobileNetDetectionNetwork, tuple[int, int]]:
    node = pipeline.createMobileNetDetectionNetwork()
    blob = dai.OpenVINO.Blob(Path("nn_models/face-detection-retail-0004_openvino_2022.1_6shave.blob").resolve())
    node.setBlob(blob)
    nn_in: dai.TensorInfo = next(iter(blob.networkInputs.values()))
    size: tuple[int, int] = (nn_in.dims[0], nn_in.dims[1])  # 300x300 for: face-detection-retail-0004_openvino_2022.1_6shave.blob
    node.setConfidenceThreshold(0.5)
    node.input.setBlocking(False)
    source.link(node.input)

    return node, size


def create_emotion_detection_nn(pipeline: dai.Pipeline, source: dai.Node.Output) -> dai.node.NeuralNetwork:
    node = pipeline.createNeuralNetwork()
    node.setBlobPath(Path("nn_models/emotions-recognition-retail-0003_openvino_2022.1_6shave.blob").resolve())  # size = 64x64
    source.link(node.input)
    return node


def create_age_gender_nn(pipeline: dai.Pipeline, source: dai.Node.Output) -> dai.node.NeuralNetwork:
    node = pipeline.createNeuralNetwork()
    node.setBlobPath(Path("nn_models/age-gender-recognition-retail-0013_openvino_2022.1_6shave.blob").resolve())
    source.link(node.input)
    return node


def create_re_id_nn(pipeline: dai.Pipeline, source: dai.Node.Output) -> dai.node.NeuralNetwork:
    node = pipeline.createNeuralNetwork()
    node.setBlobPath(Path("nn_models/person-reidentification-retail-0288_openvino_2022.1_6shave.blob").resolve())
    source.link(node.input)
    return node


def create_object_tracker(pipeline: dai.Pipeline, image_source: dai.Node.Output, detections_source: dai.Node.Output) -> dai.node.ObjectTracker:
    object_tracker = pipeline.createObjectTracker()
    object_tracker.setTrackerType(dai.TrackerType.ZERO_TERM_COLOR_HISTOGRAM)
    object_tracker.setDetectionLabelsToTrack([0])  # 0 for people
    object_tracker.setTrackerIdAssignmentPolicy(dai.TrackerIdAssignmentPolicy.UNIQUE_ID)
    image_source.link(object_tracker.inputDetectionFrame)
    image_source.link(object_tracker.inputTrackerFrame)
    detections_source.link(object_tracker.inputDetections)
    return object_tracker


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


def create_image_manip_bare(pipeline: dai.Pipeline, source: dai.Node.Output) -> dai.node.ImageManip:
    image_manip = pipeline.createImageManip()
    source.link(image_manip.inputImage)
    return image_manip


def create_output(pipeline, node: dai.Node.Output, stream_name: str):
    xout = pipeline.createXLinkOut()
    xout.setStreamName(stream_name)
    node.link(xout.input)


def create_h264_encoder(pipeline: dai.Pipeline, fps):
    rh_encoder = pipeline.createVideoEncoder()
    rh_encoder_profile = dai.VideoEncoderProperties.Profile.H264_MAIN
    rh_encoder.setDefaultProfilePreset(fps, rh_encoder_profile)
    rh_encoder.input.setQueueSize(2)
    rh_encoder.input.setBlocking(False)
    rh_encoder.setKeyframeFrequency(fps)
    rh_encoder.setRateControlMode(dai.VideoEncoderProperties.RateControlMode.CBR)
    rh_encoder.setNumFramesPool(3)
    return rh_encoder


def create_mjpeg_encoder(pipeline: dai.Pipeline, fps: int):
    encoder = pipeline.createVideoEncoder()
    encoder_profile = dai.VideoEncoderProperties.Profile.MJPEG
    encoder.setDefaultProfilePreset(fps, encoder_profile)
    return encoder



