import time

from geometry import BoundingBox
from settings import IMAGE_HEIGHT, IMAGE_WIDTH

from robothub_core import STREAMS, StreamHandle

LiveViewTexts = list[tuple[str, tuple[int, int]]]
LiveViewRois = list[tuple[tuple[int, int, int, int], str]]


def create_stream_handle(camera_serial: str, unique_key: str, description: str):
    if unique_key not in STREAMS.streams:
        color_stream_handle = STREAMS.create_video(camera_serial, unique_key, description)
    else:
        color_stream_handle = STREAMS.streams[unique_key]
    return color_stream_handle


def destroy_stream_handle(stream_handle: StreamHandle):
    STREAMS.destroy(stream=stream_handle)


OverlayData = list[tuple[BoundingBox, str, tuple[int, int, int]]]  # bbox, label, color


def publish_stream(stream_handle, overlay_data: OverlayData, rois: LiveViewRois, texts: LiveViewTexts, h264_encoded,
                   frame_width: int, frame_height: int):

    timestamp = int(time.time() * 1_000)
    metadata = {
        "platform": "robothub",
        "frame_shape": [frame_height, frame_width],
        "config": {
            "output": {
                "img_scale": 1.0,
                "show_fps": False,
                "clickable": True
            },
            "detection": {
                "thickness": 1,
                "fill_transparency": 0.2,
                "box_roundness": 20,
                "color": [255, 255, 255],
                "bbox_style": 1,
                "line_width": 0.5,
                "line_height": 0.5,
                "hide_label": False,
                "label_position": 30,
                "label_padding": 10
            },
            'text': {
                'font_color': [0, 0, 0],
                'font_transparency': 1.,
                'font_scale': 1.6,
                'font_thickness': 2,
                'bg_transparency': 1.,
                'bg_color': [249, 249, 249]
            }
        },
        "objects": [
            {
                "type": "detections",
                "detections": []
            }
        ]
    }
    live_view_ratio_w = frame_width / IMAGE_WIDTH
    live_view_ratio_h = frame_height / IMAGE_HEIGHT
    for overlay_data in overlay_data:
        bbox, label, color = overlay_data
        metadata["objects"][0]["detections"].append({'bbox': [bbox.xmin * live_view_ratio_w, bbox.ymin * live_view_ratio_h,
                                                              bbox.xmax * live_view_ratio_w, bbox.ymax * live_view_ratio_h],
                                                     'label': label, 'color': color})
    for roi, label in rois:
        xmin, ymin, xmax, ymax = roi
        metadata["objects"][0]["detections"].append({'bbox': [xmin * live_view_ratio_w, ymin * live_view_ratio_h,
                                                              xmax * live_view_ratio_w, ymax * live_view_ratio_h],
                                                     'label': label, 'color': [0, 255, 255]})

    for live_view_text in texts:
        text, position = live_view_text
        metadata["objects"].append({'type': "text", 'coords': position, "text": text})
    stream_handle.publish_video_data(bytes(h264_encoded), timestamp, metadata)


class LiveView:

    def __init__(self, camera_serial: str, unique_key: str, description: str):
        self.frame_width = IMAGE_WIDTH
        self.frame_height = IMAGE_HEIGHT
        self.unique_key = unique_key
        self.description = description

        # text display
        self.exposure = 0
        self.iso = 0
        self.focus = 0
        self.direction_of_travel = "None"

        self.stream_handle = create_stream_handle(camera_serial=camera_serial, unique_key=unique_key, description=description)
        self.overlay_data: OverlayData = []
        self.texts: LiveViewTexts = []
        self.rois: LiveViewRois = []

    def set_bboxes(self, overlay_data: OverlayData) -> None:
        self.overlay_data = overlay_data

    def set_rois(self, rois: LiveViewRois) -> None:
        self.rois = rois

    def set_texts(self, texts: LiveViewTexts) -> None:
        self.texts = texts

    def publish(self, image_h264) -> None:
        publish_stream(stream_handle=self.stream_handle, overlay_data=self.overlay_data, rois=self.rois, texts=self.texts, h264_encoded=image_h264,
                       frame_width=self.frame_width, frame_height=self.frame_height)

    def destroy(self) -> None:
        destroy_stream_handle(stream_handle=self.stream_handle)
