from pathlib import Path
import depthai as dai
import robothub as rh

# TODO: put to config?
CONFIDENCE_THRESHOLD = 0.2
NUMBER_OF_CROPPED_IMAGES = 9
NN_INPUT_SIZE_W = 512
NN_INPUT_SIZE_H = 288
crop_vals = [(0.0, 0.0), (0.0, 0.3), (0.0, 0.6), (0.3, 0.0), (0.3, 0.3), (0.3, 0.6), (0.6, 0.0), (0.6, 0.3), (0.6, 0.6)]

# ImageManip nodes with corresponding configs
# https://docs.luxonis.com/projects/api/en/latest/components/nodes/image_manip/
def create_image_manip(pipeline: dai.Pipeline, crop):
    # create the node
    manip = pipeline.create(dai.node.ImageManip)
    
    # default config values
    manip.initialConfig.setFrameType(dai.ImgFrame.Type.BGR888p)
    manip.initialConfig.setResize(NN_INPUT_SIZE_W, NN_INPUT_SIZE_H)
    step = 0.4
    xmin = crop[0]
    ymin = crop[1]
    xmax = xmin + step
    ymax = ymin + step
    manip.initialConfig.setCropRect(xmin, ymin, xmax, ymax)
    
    # input image settings
    manip.inputImage.setWaitForMessage(True)
    manip.inputImage.setBlocking(True)
    manip.inputImage.setQueueSize(1)
    manip.setMaxOutputFrameSize(NN_INPUT_SIZE_W * NN_INPUT_SIZE_H * 3)

    return manip


def create_nn_yolo(pipeline: dai.Pipeline):
    # YoloDetectionNetwork
    # https://docs.luxonis.com/projects/api/en/latest/components/nodes/yolo_detection_network/
    node = pipeline.create(dai.node.YoloDetectionNetwork)
    node.setBlobPath(str((Path(__file__).parent / Path('qr_model_512x288_rvc2_openvino_2022.1_6shave.blob')).resolve().absolute()))
    node.setConfidenceThreshold(CONFIDENCE_THRESHOLD)
    node.setNumClasses(1)
    node.setCoordinateSize(4)
    node.setIouThreshold(0.5)
    node.setNumInferenceThreads(2)
    node.input.setBlocking(True)  # set blocking, otherwise configs in queue might be overwritten
    node.input.setQueueSize(50)
    return node


def create_pipeline(pipeline: dai.Pipeline):
    # choose image source
    if rh.CONFIGURATION["replay"]:
        rgb_input = create_rgb_replay(pipeline=pipeline, fps=rh.CONFIGURATION["fps"], replay_directory="replays")
    else:
        rgb_input = create_rgb_sensor(pipeline=pipeline, fps=rh.CONFIGURATION["fps"])

    rgb_input_control = pipeline.createXLinkIn()
    rgb_input_control.setStreamName("rgb_input_control")
    rgb_input_control.out.link(rgb_input.inputControl)
    rgb_h264_encoder = create_h264_encoder(pipeline=pipeline, fps=rh.CONFIGURATION["fps"])
    rgb_mjpeg_encoder = create_mjpeg_encoder(pipeline=pipeline, fps=rh.CONFIGURATION["fps"])

    # Script
    # https://docs.luxonis.com/projects/api/en/latest/components/nodes/script/
    script = pipeline.create(dai.node.Script)
    # wait for the output of the corresponding image manip and send it to the NN,
    # making sure the frames are passed in the right order
    script.setScript("""
        import time
        
        NUMBER_OF_CROPPED_IMAGES = 9

        while True:
            for i in range(NUMBER_OF_CROPPED_IMAGES):
                input_name = f"in_manip{i}"
                frame = node.io[input_name].get()
                node.io['out_frame'].send(frame)
    """)

    # linking
    rgb_input.video.link(rgb_h264_encoder.input)
    rgb_input.video.link(rgb_mjpeg_encoder.input)

    # connect the camera preview to each image manip's input,
    # connect each image manip's output to the Script node's input
    for i in range(NUMBER_OF_CROPPED_IMAGES):
        im = create_image_manip(pipeline, crop_vals[i])
        
        # camera (preview) > image manip
        rgb_input.preview.link(im.inputImage)

        # image manip > script
        input_name = f"in_manip{i}"
        im.out.link(script.inputs[input_name])

        # script input settings
        script.inputs[input_name].setBlocking(True)
        script.inputs[input_name].setQueueSize(1)

    # detection nn
    nn_yolo = create_nn_yolo(pipeline)

    # script -> NN
    script.outputs['out_frame'].link(nn_yolo.input)

    # XLinkOut (NN output)
    # https://docs.luxonis.com/projects/api/en/latest/components/nodes/xlink_out/
    xout_nn = pipeline.create(dai.node.XLinkOut)
    xout_nn.setStreamName("nn")

    # NN -> out (host)
    nn_yolo.out.link(xout_nn.input)  # detections

    # outputs
    create_output(pipeline=pipeline, node=rgb_h264_encoder.bitstream, stream_name="rgb_h264")
    create_output(pipeline=pipeline, node=rgb_mjpeg_encoder.bitstream, stream_name="rgb_mjpeg")

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


def create_rgb_replay(pipeline: dai.Pipeline, fps: float, replay_directory: str,
                      run_in_loop: bool = True, start: int = None, end: int = None) -> rh.ColorReplayCamera:
    # replay_files = [os.path.join(replay_directory, f) for f in os.listdir(replay_directory)]
    replay_files = "replays/cut.mp4"
    node = rh.ColorReplayCamera(pipeline=pipeline, fps=fps, src=replay_files, run_in_loop=run_in_loop, start=start,
                                end=end)
    node.setInterleaved(False)
    node.setVideoSize(1920, 1080)
    node.setPreviewSize(1920, 1080)
    node.setFps(fps)
    return node


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


def create_mjpeg_encoder(pipeline: dai.Pipeline, fps: float) -> dai.node.VideoEncoder:
    encoder = pipeline.createVideoEncoder()
    encoder_profile = dai.VideoEncoderProperties.Profile.MJPEG
    encoder.setDefaultProfilePreset(fps, encoder_profile)
    return encoder

def create_output(pipeline: dai.Pipeline, node: dai.Node.Output, stream_name: str):
    xout = pipeline.createXLinkOut()
    xout.setStreamName(stream_name)
    node.link(xout.input)
