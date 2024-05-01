import blobconverter
import depthai as dai
import robothub as rh

CAM_SIZE = (2144, 2144)
NN_SIZE = (256, 256)


def create_output(pipeline: dai.Pipeline, input: dai.Node.Output, stream_name: str):
    xout = pipeline.createXLinkOut()
    xout.setStreamName(stream_name)
    input.link(xout.input)
    return xout


def create_pipeline():
    pipeline = dai.Pipeline()
    version = "2021.2"
    pipeline.setOpenVINOVersion(version=dai.OpenVINO.Version.VERSION_2021_2)

    color_cam: dai.node.ColorCamera = pipeline.create(dai.node.ColorCamera)
    color_cam.setResolution(dai.ColorCameraProperties.SensorResolution.THE_4_K)
    color_cam.setPreviewSize(NN_SIZE)
    color_cam.setVideoSize(CAM_SIZE)
    color_cam.setInterleaved(False)
    color_cam.setBoardSocket(dai.CameraBoardSocket.RGB)
    color_cam.setFps(rh.CONFIGURATION["fps"])

    h264_encoder: dai.node.VideoEncoder = pipeline.create(dai.node.VideoEncoder)
    h264_encoder.setDefaultProfilePreset(
        color_cam.getFps(), dai.VideoEncoderProperties.Profile.H264_MAIN
    )
    color_cam.video.link(h264_encoder.input)

    nn = pipeline.create(dai.node.NeuralNetwork)
    nn.setBlobPath(
        blobconverter.from_zoo(
            name="east_text_detection_256x256",
            zoo_type="depthai",
            shaves=6,
            version=version,
        )
    )
    color_cam.preview.link(nn.input)

    create_output(pipeline, nn.out, "nn_out")
    create_output(pipeline, color_cam.video, "color_out")
    create_output(pipeline, h264_encoder.bitstream, "h264_out")

    return pipeline
