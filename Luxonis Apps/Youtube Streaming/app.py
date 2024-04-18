import logging as log
import subprocess as sp
from typing import List

import depthai as dai
import robothub as rh
from pipeline import create_pipeline


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

    def publish_frame(self, img_frame: dai.ImgFrame):
        frame_data = img_frame.getCvFrame().tobytes()  # Retrieving frame data from the packet
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


class Application(rh.BaseDepthAIApplication):
    def __init__(self):
        super().__init__()
        self.youtube_streaming = YouTubeStreaming(self.config['streaming_key'])

    def setup_pipeline(self) -> dai.Pipeline:
        pipeline = dai.Pipeline()
        create_pipeline(pipeline=pipeline)
        return pipeline

    def manage_device(self, device: dai.Device):
        log.info(f"DepthAi version: {dai.__version__}")
        log.info(f"Oak started. getting queues...")
        rgb_h264 = device.getOutputQueue(name="rgb_h264", maxSize=5, blocking=False)

        while rh.app_is_running and self.device_is_running:
            try:
                rgb_h264_frame: dai.ImgFrame = rgb_h264.get()
            except RuntimeError as e:
                log.error(f"OAK disconnected. Restarting. Error while getting frame from queue: {e}")
                self.restart_device()
            self.youtube_streaming.publish_frame(rgb_h264_frame)


if __name__ == "__main__":
    app = Application()
    app.run()
