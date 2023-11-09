import subprocess as sp
from typing import List

from depthai_sdk import OakCamera
from robothub.application import BaseApplication


class YouTubeStreaming:
    proc: sp.Popen = None  # Subprocess for streaming

    def __init__(self, key: str):
        if not key or key == 'placeholder':
            raise Exception('Please define a valid streaming key.')

        command = self.make_command(key) + ['-loglevel', 'quiet']
        # If you want to see logs from ffmpeg, use the following arguments instead:
        # ['-loglevel', 'quiet', '-report'] or ['-loglevel', 'error']

        if self.proc:
            self.proc.kill()  # Terminating the current subprocess if it exists

        self.proc = sp.Popen(command, stdin=sp.PIPE, stderr=None)  # Launching a new streaming subprocess

    def process_packets(self, packet):
        frame_data = packet.msg.getData()  # Retrieving frame data from the packet 
        self.proc.stdin.write(frame_data)  # Passing frame data to the stdin of the streaming subprocess 
        self.proc.stdin.flush()  # Flushing stdin buffer

    @staticmethod
    def make_command(key: str) -> List[str]:
        HLS_URL = f"https://a.upload.youtube.com/http_upload_hls?cid={key}&copy=0&file=stream.m3u8"

        hls_command = ["ffmpeg",
                       '-hide_banner',
                       "-fflags", "+genpts",
                       '-loglevel', 'info',
                       '-use_wallclock_as_timestamps', 'true',
                       '-thread_queue_size', '512',
                       "-i", "-",
                       "-f", "lavfi",
                       '-thread_queue_size', '512',
                       "-i", "anullsrc",
                       "-c:v", "copy",
                       "-c:a", "aac",
                       "-f", "hls",
                       "-hls_time", "2",
                       "-hls_list_size", "4",
                       "-http_persistent", "1",
                       "-method", "PUT",
                       HLS_URL]

        return hls_command


class Application(BaseApplication):
    """
    This is an example application that streams video to YouTube. It is intended to be used with a single device.
    """

    def __init__(self):
        super().__init__()
        self.youtube_streaming = YouTubeStreaming(self.config['streaming_key'])

    def setup_pipeline(self, oak: OakCamera):
        """
        Define your data pipeline. Can be called multiple times during runtime. Make sure that objects that have to be created only once
        are defined either as static class variables or in the __init__ method of this class.
        """
        color = oak.create_camera(source='color', fps=self.config['fps'], resolution='1080p', encode='h264')
        detection_nn = oak.create_nn(model='yolov6nr3_coco_640x352', input=color)
        oak.callback(detection_nn.out.encoded, self.youtube_streaming.process_packets)
