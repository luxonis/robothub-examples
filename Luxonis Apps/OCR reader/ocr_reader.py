import easyocr
import numpy as np
from model import TextDetection
from pipeline import CAM_SIZE, NN_SIZE

DETECTION_CONF_THRESHOLD = 0.5
RECOGNITION_CONF_THRESHOLD = 0.7
VISUALIZATION_CONF_THRESHOLD = 0.3
CHAR_LIST = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ "


class OcrReader:
    def __init__(self) -> None:
        self._reader = easyocr.Reader(["en"], detector=False)
        self._current_detections: list[TextDetection] | None = None

        self._input_rect_points: list[list[tuple[int, int]]] | None = None
        self._input_image: np.ndarray | None = None

    def set_input_data(
        self, rect_points: list[list[tuple[int, int]]], image: np.ndarray
    ):
        self._input_rect_points = rect_points
        self._input_image = image
        self._current_detections = None

    def _recognize_text(
        self, rect_points: list[list[tuple[int, int]]], image: np.ndarray
    ) -> list[TextDetection]:
        """Run text recognition on text detections received from EAST neural network."""

        scaling = np.asarray(CAM_SIZE) / np.asarray(NN_SIZE)
        scaled_rotated_points = []
        # Convert angled bboxes to horizontal bboxes
        for rp in rect_points:
            # Detections are done on 256x256 frames, we are sending back 1024x1024
            # That's why we rescale points
            scaled_points = (rp * scaling).astype(int).tolist()
            scaled_rotated_points.append(scaled_points)
        detections = self._reader.recognize(
            image,
            horizontal_list=[],
            free_list=scaled_rotated_points,
            allowlist=CHAR_LIST,
            decoder="beamsearch",
            beamWidth=5,
        )
        parsed_detections = [
            TextDetection(bbox_points=d[0], text=d[1], confidence=d[2])
            for d in detections
        ]
        return parsed_detections

    def get_current_detections(
        self, min_confidence: float = 0.0
    ) -> list[TextDetection]:
        """Returns all detections in current input data with confidence higher than `min_confidence`"""

        if self._input_rect_points is None or self._input_image is None:
            raise RuntimeError("Missing input data")

        if self._current_detections is None:
            self._current_detections = self._recognize_text(
                self._input_rect_points, self._input_image
            )

        # Filter detections below min confidence threshold
        filtered_detections = [
            det for det in self._current_detections if det.confidence >= min_confidence
        ]
        return filtered_detections

    def get_current_detections_as_string(self, min_confidence: float = 0.0) -> str:
        """Returns all detections in current input data with confidence higher than `min_confidence` as a string"""

        detections = self.get_current_detections(min_confidence)
        text_with_centroids = []
        for det in detections:
            bbox_arr = np.asarray(det.bbox_points)
            bbox_centroid = np.mean(bbox_arr, axis=0)
            text_with_centroids.append((det.text, bbox_centroid))
        sorted_text = sorted(text_with_centroids, key=lambda t: (t[1][1], t[1][0]))
        return " ".join(i[0] for i in sorted_text)

    def get_query_detections(self):
        """Returns detections, that should be used as an Open Library query"""
        return self.get_current_detections(RECOGNITION_CONF_THRESHOLD)

    def get_query_text(self):
        """Returns text of the Open Library query"""
        return self.get_current_detections_as_string(RECOGNITION_CONF_THRESHOLD)

    def get_visualization_bboxes(self):
        """Returns bboxes that should be visualized"""
        return [
            i.bbox_points
            for i in self.get_current_detections(VISUALIZATION_CONF_THRESHOLD)
        ]

    def get_query_bboxes(self):
        """Returns bboxes of detections, that should be used as Open Library query"""
        return [
            i.bbox_points
            for i in self.get_current_detections(RECOGNITION_CONF_THRESHOLD)
        ]
