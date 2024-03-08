from pathlib import Path

import depthai as dai

BLOB_PATH = Path("/app/yolov6nr4-512x320-rvc3.blob")


def build_pipeline(front_socket: dai.CameraBoardSocket, front_stream_name, rear_socket, rear_stream_name)-> dai.Pipeline:
    pipeline = dai.Pipeline()

    def add_side(socket: dai.CameraBoardSocket, stream_name):
        rgb = pipeline.create(dai.node.ColorCamera)
        rgb.setBoardSocket(socket)
        rgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_800_P)
        rgb.setInterleaved(False)
        rgb.setPreviewSize(512, 320)
        rgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
        rgb.setFps(8) 

        h264_encoder = pipeline.create(dai.node.VideoEncoder)
        h264_encoder.setDefaultProfilePreset(8, dai.VideoEncoderProperties.Profile.H264_MAIN)
        h264_encoder.setQuality(50)
        h264_encoder.setKeyframeFrequency(30)
        h264_encoder.setBitrateKbps(1800)
        h264_encoder.input.setQueueSize(1)
        rgb.video.link(h264_encoder.input)

        xout_color_h264 = pipeline.create(dai.node.XLinkOut)
        xout_color_h264.setStreamName(stream_name)
        xout_color_h264.input.setBlocking(False)
        h264_encoder.bitstream.link(xout_color_h264.input)
        

        detectionNetwork = pipeline.createYoloDetectionNetwork()
        detectionNetwork.setConfidenceThreshold(0.6)
        detectionNetwork.setNumClasses(80)
        detectionNetwork.setCoordinateSize(4)
        detectionNetwork.setIouThreshold(0.5)
        detectionNetwork.setBlobPath(BLOB_PATH)
        detectionNetwork.setNumInferenceThreads(8)
        detectionNetwork.input.setBlocking(False)
        detectionNetwork.input.setQueueSize(1)
        rgb.preview.link(detectionNetwork.input)


        xout_nn = pipeline.create(dai.node.XLinkOut)
        xout_nn.input.setBlocking(False)
        xout_nn.setStreamName(f"{stream_name}_nn")
        detectionNetwork.out.link(xout_nn.input)
        xoutPTNN = pipeline.create(dai.node.XLinkOut)
        xoutPTNN.setStreamName(f"{stream_name}_nn_pt")
        detectionNetwork.passthrough.link(xoutPTNN.input)

    add_side(front_socket, front_stream_name)
    add_side(rear_socket, rear_stream_name)
    return pipeline
