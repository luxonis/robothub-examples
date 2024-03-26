import logging as log
import os
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

import av
import cv2
import depthai as dai
import numpy as np
import robothub as rh


class Video:

    def __init__(self):
        self.codec_r = av.CodecContext.create("h264", "r")

    @staticmethod
    def create_video_from_frames(frames_bgr: list[np.ndarray], output_file: str):
        fps = 9
        if not frames_bgr:
            log.warning(f"No frames to save to {output_file}")
            return
        height, width = frames_bgr[0].shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for .mp4
        video = cv2.VideoWriter(output_file, fourcc, fps, (width, height))

        for img_bgr in frames_bgr:
            video.write(img_bgr)

        video.release()

    @staticmethod
    def read_as_bytes(filename: str) -> bytes:
        with open(filename, "rb") as f:
            video_bytes = f.read()
        return video_bytes

    @staticmethod
    def delete_video_file(filename: str) -> None:
        try:
            os.remove(filename)
        except FileNotFoundError:
            pass

    def h264_to_bgr(self, frames: list[dai.ImgFrame]) -> list[np.ndarray]:
        result = []
        for frame in frames:
            frame: dai.ImgFrame
            image = frame.getCvFrame()
            bgr_frame = self._decode_h264_image(image=image)
            if bgr_frame is None:
                # create gray image - we have other data for every frame, so if the sequence doesn't start with a key frame
                # then use gray as placeholders
                bgr_frame = np.full((1080, 1920, 3), 128, dtype=np.uint8)
            result.append(bgr_frame)
        return result

    def _decode_h264_image(self, image: np.ndarray) -> Optional[np.ndarray]:
        if self.codec_r is None:
            return None
        enc_packets = self.codec_r.parse(image)
        if len(enc_packets) == 0:
            return None

        try:
            frames = self.codec_r.decode(enc_packets[-1])
        except Exception:
            return None

        if not frames:
            return None

        decoded_frame = frames[0].to_ndarray(format='bgr24')
        return decoded_frame


class TimeEvent:
    monotonic: float
    wallclock: datetime

    @staticmethod
    def zero():
        return TimeEvent(0, datetime.min)

    def __init__(self, monotonic: float = None, wallclock: datetime = None):
        self.monotonic = monotonic if monotonic is not None else time.monotonic()
        self.wallclock = wallclock if wallclock is not None else datetime.now()

    def seconds_elapsed(self):
        return time.monotonic() - self.monotonic if self.monotonic > 0 else 0

    def reset(self):
        self.monotonic = time.monotonic()
        self.wallclock = datetime.now()

    def __str__(self):
        return "" if self.wallclock == datetime.min else self.wallclock.isoformat()

    def __float__(self):
        return self.monotonic

    def __bool__(self):
        return self.monotonic != 0

    def __eq__(self, other):
        return self.monotonic == other.monotonic

    def __le__(self, other):
        return self.monotonic <= other.monotonic

    def __lt__(self, other):
        return self.monotonic < other.monotonic

    def __ge__(self, other):
        return self.monotonic >= other.monotonic

    def __gt__(self, other):
        return self.monotonic > other.monotonic
