import av
import io
import logging as log
import time
from typing import Optional

import depthai as dai
import robothub as rh
from app_pipeline import host_node
from app_pipeline.messages import VideoBufferMessage


class VideoEvent(host_node.BaseNode):

    def __init__(self, input_node: host_node.BaseNode):
        super().__init__()
        input_node.set_callback(callback=self.__callback)

    def __callback(self, message: VideoBufferMessage) -> None:
        video_bytes = self.save_video(data=message.buffer.data)
        if video_bytes is None:
            return
        rh.send_video_event(video=video_bytes.getvalue(), title="video")

    def save_video(self, data: list[dai.ImgFrame]) -> Optional[io.BytesIO]:
        print(f"Saving video...")
        length = len(data)
        minimum_length = rh.CONFIGURATION["fps"] * 2
        if length < minimum_length:
            log.error(f"Video buffer is too short: {length / rh.CONFIGURATION['fps']} seconds. Minimum length: 2 seconds")
            return None

        save_start = time.monotonic()
        input_file = io.BytesIO(b"".join([frame.getCvFrame() for frame in data]))
        mp4_file = io.BytesIO()

        with av.open(mp4_file, "w", format="mp4") as output_container, av.open(input_file, "r", format="h264") as input_container:
            input_stream = input_container.streams[0]
            output_stream = output_container.add_stream(template=input_stream, rate=rh.CONFIGURATION["fps"])

            frame_time = (1 / rh.CONFIGURATION["fps"]) * input_stream.time_base.denominator
            for i, packet in enumerate(input_container.demux(input_stream)):
                packet.dts = i * frame_time
                packet.pts = i * frame_time
                packet.stream = output_stream
                output_container.mux_one(packet)
        log.info(f"Video saved, size: {len(mp4_file.getvalue()) / 1024 / 1024:.1f} MB took {time.monotonic() - save_start:.2f} seconds")

        mp4_file.flush()
        mp4_file.seek(0)
        return mp4_file



