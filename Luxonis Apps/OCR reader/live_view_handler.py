import numpy as np
import robothub as rh


class LiveViewHandler:
    def __init__(self, name: str, unique_key: str, width: int, height: int) -> None:
        self.live_view = rh.DepthaiLiveView(name, unique_key, width, height)

    def draw_points(
        self,
        points: list[tuple[int, int]],
        color: tuple[int, int, int],
        thickness: int = 1,
    ):
        for i in range(len(points) - 1):
            pt1 = points[i]
            pt2 = points[i + 1]
            self.live_view.add_line(pt1, pt2, color, thickness=thickness)
        self.live_view.add_line(points[0], points[-1], color, thickness=thickness)

    def publish_live_view_frame(
        self,
        h264_frame: np.ndarray,
        detection_bboxes: list[list[tuple[int, int]]],
        searched_detection_bboxes: list[list[tuple[int, int]]],
    ):
        # Draw detections, that are currently being searched
        for res in searched_detection_bboxes:
            bbox_arr = np.asarray(res)

            min_x = int(np.min(bbox_arr[:, 0]))
            min_y = int(np.min(bbox_arr[:, 1]))
            max_x = int(np.max(bbox_arr[:, 0]))
            max_y = int(np.max(bbox_arr[:, 1]))
            hor_bbox = (min_x, min_y, max_x, max_y)
            self.live_view.add_rectangle(hor_bbox, "")

        # Draw all detections
        for det in detection_bboxes:
            self.draw_points(det, (255, 255, 0), 1)
        self.live_view.publish(h264_frame)
