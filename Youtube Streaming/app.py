import subprocess as sp

from robothub_oak.application import RobotHubApplication
from robothub_oak import LiveView
from robothub_oak.data_processors import BaseDataProcessor
import utils


class YouTubeStreaming(BaseDataProcessor):
    def __init__(self, packet):
        self.proc = None  # Subprocess for streaming

        command = utils.make_command(self.key) + ['-loglevel', 'quiet']  # If you want to see logs from ffmpeg, use the following arguments instead:
        # ['-loglevel', 'quiet', '-report'] or ['-loglevel', 'error']

        if self.proc:
            self.proc.kill()  # Terminating the current subprocess if it exists

        self.proc = sp.Popen(command, stdin=sp.PIPE, stderr=None)  # Launching a new streaming subprocess

    def process_packets(self, packet):
        frame_data = packet.msg.getData()  # Retrieving frame data from the packet 
        self.proc.stdin.write(frame_data)  # Passing frame data to the stdin of the streaming subprocess 
        self.proc.stdin.flush()  # Flushing stdin buffer


class ExampleApplication(RobotHubApplication):
    def __init__(self):
        super().__init__()
        self.youtube_streaming = YouTubeStreaming()

        # Extracting streaming settings from robothub.CONFIGURATION
        self.bitrate = robothub.CONFIGURATION['bitrate']  # Bitrate for streaming
        self.fps = robothub.CONFIGURATION['fps']  # Frames per second for streaming
        self.key = robothub.CONFIGURATION['streaming_key']  # Streaming key
        # Check if streaming key is valid
        if not self.key or self.key == 'placeholder':
            raise Exception('Please define a valid streaming key.')

    def setup_pipeline(self, device: OakCamera):
        """This method is the entrypoint for each device and is called upon connection."""
        color = device.create_camera(source='color', fps=30, resolution='1080p', encode='h264')
        detection_nn = device.create_nn(model='yolov6nr3_coco_640x352', input=color)

        device.callback(detection_nn.out.encoded, self.youtube_streaming)

    