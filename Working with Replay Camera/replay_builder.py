import time

import av
import cv2
import depthai as dai
import numpy as np
import robothub as rh
from robothub import CONFIGURATION
from robothub.replay import ReplayBuilder


class Application(rh.BaseDepthAIApplication):
    def __init__(self):
        super().__init__()

    def on_start(self):
        super().on_start()

    def create_h264_encoder(self, pipeline: dai.Pipeline, source: dai.Node.Output, fps: int):
        rh_encoder = pipeline.createVideoEncoder()
        rh_encoder_profile = dai.VideoEncoderProperties.Profile.H264_MAIN
        rh_encoder.setDefaultProfilePreset(fps, rh_encoder_profile)
        rh_encoder.input.setQueueSize(2)
        rh_encoder.input.setBlocking(False)
        rh_encoder.setKeyframeFrequency(fps)
        rh_encoder.setRateControlMode(dai.VideoEncoderProperties.RateControlMode.CBR)
        rh_encoder.setNumFramesPool(3)
        source.link(rh_encoder.input)
        return rh_encoder

    def create_output(self, pipeline, node: dai.Node.Output, stream_name: str):
        xout = pipeline.createXLinkOut()
        xout.setStreamName(stream_name)
        node.link(xout.input)

    def setup_pipeline(self) -> dai.Pipeline:
        pipeline = dai.Pipeline()

        self.replay_camera = ReplayBuilder(pipeline, CONFIGURATION["fps"]).files("vids/*.mp4").build_color_camera()
        # Or search for all mp4 files in all subdirectories
        # self.replay_camera = ReplayBuilder(pipeline, CONFIGURATION["fps"]).recursive_files("**/*.mp4").build_color_camera()
        # You can set files to the directory with images:
        # self.replay_camera = ReplayBuilder(pipeline, CONFIGURATION["fps"]).files("vids/frames/").build_color_camera()

        rgb_h264_encoder = self.create_h264_encoder(
            pipeline=pipeline, source=self.replay_camera.video, fps=CONFIGURATION["fps"]
        )

        self.create_output(
            pipeline=pipeline,
            node=rgb_h264_encoder.bitstream,
            stream_name="rgb_preview",
        )

        return pipeline

    def manage_device(self, device: dai.Device):
        rgb_preview_queue = device.getOutputQueue(name="rgb_preview", maxSize=5, blocking=True)

        self.codec_r = av.CodecContext.create("h264", "r")

        def decode_h264_frame(frame) -> np.ndarray | None:
            enc_packets = self.codec_r.parse(frame)
            if len(enc_packets) == 0:
                return None

            try:
                frames = self.codec_r.decode(enc_packets[-1])
            except Exception:
                return None

            if not frames:
                return None

            decoded_frame = frames[0].to_ndarray(format="bgr24")
            return decoded_frame

        while rh.app_is_running():
            if rgb_preview_queue.has():
                rgb_frame: dai.ImgFrame = rgb_preview_queue.get()  # type: ignore
                frame = decode_h264_frame(rgb_frame.getCvFrame())
                if frame is not None:
                    cv2.imshow("frame", frame)

                key = cv2.waitKey(1)

                if key == ord("q"):
                    exit(0)

            time.sleep(0.001)


if __name__ == "__main__":
    app = Application()
    app.run()
