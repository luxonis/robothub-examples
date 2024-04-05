import time
from typing import List

import av
import cv2
import depthai as dai
import numpy as np
import robothub as rh
from robothub import CONFIGURATION
from robothub.replay import ColorReplayCamera, ReplayBuilder

NUM_OF_CAMERAS = 2


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

        self.cameras: List[ColorReplayCamera] = []
        for i in range(NUM_OF_CAMERAS):
            video_index = i + 1
            self.cameras.append(
                ReplayBuilder(pipeline, CONFIGURATION["fps"]).files(f"vids/*{video_index}.mp4").build_color_camera()
            )

        for i, camera in enumerate(self.cameras):
            camera.setBoardSocket(dai.CameraBoardSocket.RGB)
            color_encoder = self.create_h264_encoder(
                pipeline=pipeline,
                source=camera.video,
                fps=CONFIGURATION["fps"],
            )
            stream_index = i + 1
            self.create_output(
                pipeline=pipeline,
                node=color_encoder.bitstream,
                stream_name=f"color_{stream_index}_preview",
            )

        return pipeline

    def manage_device(self, device: dai.Device):
        queues = []
        codecs = []
        for i in range(NUM_OF_CAMERAS):
            queue_index = i + 1
            queues.append(device.getOutputQueue(name=f"color_{queue_index}_preview", maxSize=5, blocking=True))
            codecs.append(av.CodecContext.create("h264", "r"))

        def decode_h264_frame(frame, codec_index: int) -> np.ndarray | None:
            codec = codecs[codec_index]
            enc_packets = codec.parse(frame)
            if len(enc_packets) == 0:
                return None

            try:
                frames = codec.decode(enc_packets[-1])
            except Exception:
                return None

            if not frames:
                return None

            decoded_frame = frames[0].to_ndarray(format="bgr24")
            return decoded_frame

        while rh.app_is_running():
            for i, queue in enumerate(queues):
                if queue.has():
                    rgb_frame: dai.ImgFrame = queue.get()  # type: ignore
                    frame = decode_h264_frame(rgb_frame.getCvFrame(), i)
                    if frame is not None:
                        cv2.imshow(f"window {i+1}", frame)

            key = cv2.waitKey(1)
            if key == ord("q"):
                exit(0)

            time.sleep(0.001)


if __name__ == "__main__":
    app = Application()
    app.run()
