from enum import Enum


class MessageName(Enum):
    GATE_CLASSIFICATION = "gate_classification"
    GATE_STATE_BUFFER = "gate_state_buffer"
    MAIN_H264 = "main_h264"
    MAIN_MJPEG = "main_mjpeg"
    SECONDARY_H264 = "secondary_h264"
    VIDEO_BUFFER = "video_buffer"
