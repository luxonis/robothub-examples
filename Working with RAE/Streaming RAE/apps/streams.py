import robothub
import time
import depthai as dai
import logging
from time import sleep
import threading


logger = logging.getLogger(__name__)
handler = logging.FileHandler("./logs/app.log")
formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def build_pipeline(streams):
    pipeline = dai.Pipeline()
    def add_side(socket, stream_name):
        rgb = pipeline.createColorCamera()
        rgb.setBoardSocket(socket)
        if socket != dai.CameraBoardSocket.CAM_A:
            rgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_800_P)
        else:
            rgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
        rgb.setInterleaved(False)
        rgb.setPreviewSize(416,416)
        rgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
        rgb.setFps(6)  # Limitation of the current preview source at 416x416 resolution

        encoder = pipeline.create(dai.node.VideoEncoder)
        encoder.setDefaultProfilePreset(8, dai.VideoEncoderProperties.Profile.H264_MAIN)
        encoder.setQuality(50)
        encoder.setKeyframeFrequency(30)
        encoder.setBitrateKbps(1800)
        encoder.input.setQueueSize(10)
        
        xout_color = pipeline.create(dai.node.XLinkOut)
        rgb.isp.link(encoder.input)
        xout_color.setStreamName(stream_name)
        xout_color.input.setBlocking(False)
        encoder.bitstream.link(xout_color.input)
       
    for socket, stream_name in streams.items():
        add_side(socket, stream_name)    
    return pipeline
     
FRONT_RIGHT_STREAM_NAME = "stream_front_right"
FRONT_LEFT_STREAM_NAME = "stream_front_left"
BACK_RIGHT_STREAM_NAME = "stream_back_right"
BACK_LEFT_STREAM_NAME = "stream_back_left"
COLOR_STREAM_NAME = "stream_color"
RESOLUTION_WIDTH = 1280
RESOLUTION_HEIGHT = 800

class Application(robothub.RobotHubApplication):
    def __init__(self):
        super().__init__()
        self.device = None
        self.stream_handles = {}
        self.available_apps = []
        self.mutex=threading.Lock()

    def on_start(self):
        if not robothub.DEVICES:
            logger.error(
                "The default app requires an assigned device to run. "
                "Please go to RobotHub, navigate to the app's page, "
                "click the \"Reassign devices\" button and select a device."
            )
            self._stop(1)
        logger.info("Starting the app...")
        sleep(2)
        logger.info("Starting streams...")
        self.init_streams()
        
    def on_stop(self):
        logger.info("Stopping the app...")
        if self.device:
            logger.info("Closing device")
            self.device.close()
            
    def init_streams(self):
        device_mxid = robothub.DEVICES[0].oak["serialNumber"]
        device_info = dai.DeviceInfo(device_mxid)
        self.device = dai.Device(device_info)

        streams = {
        dai.CameraBoardSocket.CAM_A: COLOR_STREAM_NAME, 
        dai.CameraBoardSocket.CAM_B: FRONT_LEFT_STREAM_NAME,
        dai.CameraBoardSocket.CAM_C: FRONT_RIGHT_STREAM_NAME,
        dai.CameraBoardSocket.CAM_D: BACK_RIGHT_STREAM_NAME,
        dai.CameraBoardSocket.CAM_E: BACK_LEFT_STREAM_NAME
        }
        
        pipeline = build_pipeline(streams)
        self.device.startPipeline(pipeline)
        
        for stream_name in streams.values():
            output_queue = self.device.getOutputQueue(name=stream_name, maxSize=1, blocking=False)
            output_queue.addCallback(self.stream_callback)
            self.stream_handles[stream_name] = robothub.STREAMS.create_video(
                device_mxid, stream_name, stream_name
            )
       
    def stream_callback(self, name: str, msg: dai.ImgFrame):
        with self.mutex:
            color_frame = msg.getData()
            metadata = {
                "platform": "robothub",
                "frame_shape": [RESOLUTION_HEIGHT, RESOLUTION_WIDTH],
            }
            timestamp = int(time.time() * 1_000)
            try:
                self.stream_handles[name].publish_video_data(bytes(color_frame), timestamp, metadata)
            except Exception as e:
                print("ERROR",e)