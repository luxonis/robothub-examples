import depthai as dai
import json

from depthai_sdk.components.nn_helper import Path
import robothub as rh
    

def create_pipeline(pipeline: dai.Pipeline, device: dai.Device) -> None:
    stereo_pairs: list[dai.StereoPair] = device.getStereoPairs()
    is_stereo_device = len(stereo_pairs) > 0

    rgb_sensor = create_rgb_sensor(pipeline, fps=rh.CONFIGURATION["fps"])
    rgb_input = pipeline.createXLinkIn()
    rgb_input.setStreamName("rgb_input")

    rgb_h264_encoder = create_h264_encoder(pipeline=pipeline, fps=rh.CONFIGURATION["fps"])
    # linking
    rgb_input.out.link(rgb_sensor.inputControl)
    rgb_sensor.video.link(rgb_h264_encoder.input)

    # detection nn
    image_manip = create_image_manip(pipeline=pipeline, source=rgb_sensor.preview, resize=(640, 640))
    detection_nn = create_detecting_nn(pipeline, "nn_models/yolov6n_openvino_2022.3_RVC3_6shave.blob", source=image_manip.out)

    # outputs
    create_output(pipeline=pipeline, node=rgb_h264_encoder.bitstream, stream_name="rgb_h264")
    create_output(pipeline=pipeline, node=detection_nn.out, stream_name="detection_nn")
    
    if is_stereo_device:
        left_sensor = create_left_sensor(pipeline, fps=rh.CONFIGURATION["fps"])
        right_sensor = create_right_sensor(pipeline, fps=rh.CONFIGURATION["fps"])

        stereo = create_stereo(pipeline)
        script = create_script_node(pipeline)
        img_manip = create_img_manip(pipeline)
        stereo_depth_encoder = create_depth_encoder(pipeline=pipeline, fps=rh.CONFIGURATION["fps"])

        # linking
        left_sensor.out.link(stereo.left)
        right_sensor.out.link(stereo.right)
        stereo.disparity.link(script.inputs['depth'])
        script.outputs['depth_out'].link(img_manip.inputImage)
        img_manip.out.link(stereo_depth_encoder.input)

        # outputs
        create_output(pipeline=pipeline, node=stereo_depth_encoder.bitstream, stream_name="stereo_depth")


def create_rgb_sensor(pipeline: dai.Pipeline, fps: float) -> dai.node.ColorCamera:
    node = pipeline.createColorCamera()
    node.setBoardSocket(dai.CameraBoardSocket.CAM_A)
    node.setInterleaved(False)
    node.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
    node.setPreviewNumFramesPool(4)
    node.setPreviewSize(1280, 720)
    node.setVideoSize(1920, 1080)
    node.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
    node.setFps(fps)
    return node


def create_left_sensor(pipeline: dai.Pipeline, fps: float) -> dai.node.MonoCamera:
    left = pipeline.create(dai.node.MonoCamera)
    left.setBoardSocket(dai.CameraBoardSocket.CAM_B)
    left.setFps(fps)
    return left


def create_right_sensor(pipeline : dai.Pipeline, fps: float) -> dai.node.MonoCamera:
    right = pipeline.create(dai.node.MonoCamera)
    right.setBoardSocket(dai.CameraBoardSocket.CAM_C)
    right.setFps(fps)
    return right


def create_stereo(pipeline: dai.Pipeline) -> dai.node.StereoDepth:
    stereo = pipeline.create(dai.node.StereoDepth)
    stereo.setDepthAlign(dai.CameraBoardSocket.CAM_A)
    stereo.initialConfig.setMedianFilter(dai.MedianFilter.KERNEL_5x5)
    stereo.initialConfig.setLeftRightCheck(True)
    config = stereo.initialConfig.get()
    config.postProcessing.decimationFilter.decimationFactor = 1
    config.postProcessing.speckleFilter.enable = False
    config.postProcessing.speckleFilter.speckleRange = 50
    config.postProcessing.temporalFilter.enable = True
    config.postProcessing.decimationFilter.decimationFactor = 1
    config.postProcessing.thresholdFilter.minRange = 400
    config.postProcessing.thresholdFilter.maxRange = 15000
    stereo.initialConfig.set(config)
    return stereo


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


def create_script_node(pipeline : dai.Pipeline):
    script = pipeline.create(dai.node.Script)
    script.setScript("""
    import cv2
    import numpy as np
    import depthai as dai
  
    while True:
        depth_out = node.io['depth'].tryGet()       

        if depth_out is not None:
              
            frame = depth_out.getCvFrame()
            frame = (frame // 12).astype(np.uint8)
        
            colormap = cv2.applyColorMap(np.arange(256, dtype=np.uint8), cv2.COLORMAP_JET)
            colormap[0] = [0, 0, 0]  # zero (invalidated) pixels as black
            frame = cv2.applyColorMap(frame, colormap)

            H, W, C = frame.shape

            # Split the interleaved image into separate channels
            B = frame[:, :, 0].reshape(H * W)
            G = frame[:, :, 1].reshape(H * W)
            R = frame[:, :, 2].reshape(H * W)

            # Stack them to create the planar image format
            frame = np.concatenate((B, G, R), axis=0)

            img = dai.ImgFrame()
            img.set(depth_out.get())
            img.setType(dai.ImgFrame.Type.BGR888p)
            img.setFrame(frame)
            img.setWidth(depth_out.getWidth())
            img.setHeight(depth_out.getHeight())
            img.setTimestamp(depth_out.getTimestamp())
            img.setInstanceNum(depth_out.getInstanceNum())

            node.io['depth_out'].send(img)
    """)
    
    return script
    
    
def create_img_manip(pipeline: dai.Pipeline) -> dai.node.ImageManip:
    colormap = pipeline.create(dai.node.ImageManip)
    colormap.initialConfig.setFrameType(dai.ImgFrame.Type.NV12)
    colormap.setMaxOutputFrameSize(1280*800*3//2)
    return colormap


def create_depth_encoder(pipeline: dai.Pipeline, fps: float) -> dai.node.VideoEncoder:
    encoder = pipeline.create(dai.node.VideoEncoder)
    encoder_profile = dai.VideoEncoderProperties.Profile.H264_MAIN
    encoder.setDefaultProfilePreset(fps, encoder_profile)
    return encoder


def create_image_manip(pipeline: dai.Pipeline, source: dai.Node.Output, resize: tuple[int, int],
                       keep_aspect_ration: bool = False,
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
    model_config = Path("nn_models/detection_config.json")
    with model_config.open() as f:
        config = json.loads(f.read())
    node = pipeline.createYoloDetectionNetwork()
    nn_metadata = config["nn_config"]["NN_specific_metadata"]
    node.setNumClasses(nn_metadata["classes"])
    node.setCoordinateSize(nn_metadata["coordinates"])
    node.setAnchors(nn_metadata["anchors"])
    node.setAnchorMasks(nn_metadata["anchor_masks"])
    node.setIouThreshold(nn_metadata["iou_threshold"])
    node.input.setBlocking(False)
    blob = dai.OpenVINO.Blob(Path(model).resolve())
    node.setBlob(blob)
    source.link(node.input)
    return node


def create_output(pipeline: dai.Pipeline, node: dai.Node.Output, stream_name: str):
    xout = pipeline.create(dai.node.XLinkOut)
    xout.setStreamName(stream_name)
    node.link(xout.input)