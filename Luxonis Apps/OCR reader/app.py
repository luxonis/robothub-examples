import logging as log
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import blobconverter
import depthai as dai
import east
import easyocr
import numpy as np
import requests
import robothub as rh


def create_output(pipeline: dai.Pipeline, input: dai.Node.Output, stream_name: str):
    xout = pipeline.createXLinkOut()
    xout.setStreamName(stream_name)
    input.link(xout.input)
    return xout


CAM_SIZE = (2144, 2144)
NN_SIZE = (256, 256)

DETECTION_CONF_THRESHOLD = 0.5
RECOGNITION_CONF_THRESHOLD = 0.7
VISUALIZATION_CONF_THRESHOLD = 0.3

MIN_SEARCH_INTERVAL = timedelta(seconds=3)
RESULT_LIMIT = 5
CHAR_LIST = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ "

# Open Library URLs
OLIB_URL = "https://openlibrary.org"
OLIB_COVER_URL = "https://covers.openlibrary.org"
COVER_PLACEHOLDER_URL = "https://openlibrary.org/images/icons/avatar_book-sm.png"
OLIB_SEARCH_URL = f"{OLIB_URL}/search.json"


class Application(rh.BaseDepthAIApplication):
    def __init__(self):
        super().__init__()
        self.thread_pool_executor = ThreadPoolExecutor(max_workers=1)

        # List of detections, that are currently being searched
        self.searched_detections = None
        self.last_successful_search = datetime.now()

        # Reader used for text recognition
        self.reader = easyocr.Reader(["en"], detector=False)

    def setup_pipeline(self) -> dai.Pipeline:
        """Define the pipeline using DepthAI."""

        log.info(f"App config: {rh.CONFIGURATION}")
        log.info("Creating camera pipeline")

        pipeline = dai.Pipeline()
        version = "2021.2"
        pipeline.setOpenVINOVersion(version=dai.OpenVINO.Version.VERSION_2021_2)

        color_cam: dai.node.ColorCamera = pipeline.create(dai.node.ColorCamera)
        color_cam.setResolution(dai.ColorCameraProperties.SensorResolution.THE_4_K)
        color_cam.setPreviewSize(NN_SIZE)
        color_cam.setVideoSize(CAM_SIZE)
        color_cam.setInterleaved(False)
        color_cam.setBoardSocket(dai.CameraBoardSocket.RGB)
        color_cam.setFps(rh.CONFIGURATION["fps"])

        h264_encoder: dai.node.VideoEncoder = pipeline.create(dai.node.VideoEncoder)
        h264_encoder.setDefaultProfilePreset(
            color_cam.getFps(), dai.VideoEncoderProperties.Profile.H264_MAIN
        )
        color_cam.video.link(h264_encoder.input)

        nn = pipeline.create(dai.node.NeuralNetwork)
        nn.setBlobPath(
            blobconverter.from_zoo(
                name="east_text_detection_256x256",
                zoo_type="depthai",
                shaves=6,
                version=version,
            )
        )
        color_cam.preview.link(nn.input)

        create_output(pipeline, nn.out, "nn_out")
        create_output(pipeline, color_cam.video, "color_out")
        create_output(pipeline, h264_encoder.bitstream, "h264_out")

        return pipeline

    def search_open_lib(self, query: str):
        """Search query on https://openlibrary.org and return results as a list of dictionaries."""

        res = requests.get(OLIB_SEARCH_URL, {"q": query, "limit": RESULT_LIMIT})
        data = res.json()
        search_results = []
        for doc in data["docs"]:
            try:
                if "cover_i" in doc:
                    cover_id = doc["cover_i"]
                    cover_url = f"{OLIB_COVER_URL}/b/id/{cover_id}-M.jpg"
                else:
                    cover_url = COVER_PLACEHOLDER_URL
                first_publish_year = doc.get("first_publish_year", None)
                book_url = f"{OLIB_URL}/{doc['key']}"
                author_urls = [f"{OLIB_URL}/authors/{i}" for i in doc["author_key"]]
                search_results.append(
                    {
                        "cover_url": cover_url,
                        "title": doc["title"],
                        "authors": doc["author_name"],
                        "first_publish_year": first_publish_year,
                        "book_url": book_url,
                        "author_urls": author_urls,
                    }
                )
            except Exception:
                log.exception("Book parsing failed")
        return search_results

    @property
    def can_search(self):
        return (
            self.searched_detections is None
            and (datetime.now() - self.last_successful_search) > MIN_SEARCH_INTERVAL
        )

    def get_text_query(self, detections: list[tuple[list[int], str, float]]):
        """Transform list of detections into a query string"""

        text_with_centroids = []
        for det in detections:
            bbox, text, conf = det
            bbox_arr = np.asarray(bbox)
            bbox_centroid = np.mean(bbox_arr, axis=0)
            text_with_centroids.append((text, bbox_centroid))
        sorted_text = sorted(text_with_centroids, key=lambda t: (t[1][1], t[1][0]))
        return " ".join(i[0] for i in sorted_text)

    def try_search_and_send_books_to_fe(
        self, detections: list[tuple[list[int], str, float]]
    ):
        """Try to search query on https://openlibrary.org. If search is successful, send results to FE."""

        def _search_inner(detections: list[tuple[list[int], str, float]]):
            log.info("Starting search")
            self.searched_detections = detections
            query = self.get_text_query(detections)

            rh.COMMUNICATOR.notify(
                "status_update", {"status": "searching", "query": query}
            )
            search_results = self.search_open_lib(query)
            if len(search_results) > 0:
                log.info("Finished search, sending results")
                self.last_successful_search = datetime.now()
                rh.COMMUNICATOR.notify(
                    "search_results", {"search_results": search_results}
                )
            else:
                log.info("Finished search, no results found")
            rh.COMMUNICATOR.notify(
                "status_update", {"status": "finished_searching", "query": query}
            )
            self.searched_detections = None

        # We use ThreadPoolExecutor to prevent blocking of the main thread, which would
        # cause displayed video streams to freeze.
        if self.can_search:
            self.thread_pool_executor.submit(_search_inner, detections)

    def recognize_text(self, nn_packet: dai.NNData, color_packet: dai.ImgFrame):
        """Run text recognition on text detections received from EAST neural network."""

        color_frame = color_packet.getCvFrame()
        boxes, angles = east.decode_east(nn_packet, RECOGNITION_CONF_THRESHOLD)
        rotated_rect_points = [
            east.get_rotated_rect_points(bbox, angle * -1)
            for (bbox, angle) in zip(boxes, angles)
        ]

        scaling = np.asarray(CAM_SIZE) / np.asarray(NN_SIZE)
        scaled_rotated_points = []
        # Convert angled bboxes to horizontal bboxes
        for rp in rotated_rect_points:
            # Detections are done on 256x256 frames, we are sending back 1024x1024
            # That's why we rescale points
            scaled_points = (rp * scaling).astype(int).tolist()
            scaled_rotated_points.append(scaled_points)

        return self.reader.recognize(
            color_frame,
            horizontal_list=[],
            free_list=scaled_rotated_points,
            allowlist=CHAR_LIST,
            decoder="beamsearch",
            beamWidth=5,
        )

    def draw_points(
        self, points: list[list[int]], color: tuple[int, int, int], thickness: int = 1
    ):
        for i in range(len(points) - 1):
            pt1 = points[i]
            pt2 = points[i + 1]
            self.live_view.add_line(pt1, pt2, color, thickness=thickness)
        self.live_view.add_line(points[0], points[-1], color, thickness=thickness)

    def publish_live_view_frame(
        self, h264_packet: dai.ImgFrame, detections: list[tuple[list[int], str, float]]
    ):
        # Draw detections, that are currently being searched
        if self.searched_detections is not None:
            for res in self.searched_detections:
                bbox, text, conf = res
                bbox_arr = np.asarray(bbox)

                min_x = int(np.min(bbox_arr[:, 0]))
                min_y = int(np.min(bbox_arr[:, 1]))
                max_x = int(np.max(bbox_arr[:, 0]))
                max_y = int(np.max(bbox_arr[:, 1]))
                hor_bbox = [min_x, min_y, max_x, max_y]
                self.live_view.add_rectangle(hor_bbox, "")

        # Draw all detections
        for det in detections:
            self.draw_points(det[0], (255, 255, 0), 1)
        self.live_view.publish(h264_packet.getCvFrame())

    def filter_detections_below_threshold(
        self, detections: list[tuple[list[int], str, float]], threshold: float
    ):
        """Remove detections with confidence lower than `RECOGNITION_CONF_THRESHOLD`."""

        return [res for res in detections if res[2] >= threshold]

    def manage_device(self, device: dai.Device):
        h264_queue: dai.DataOutputQueue = device.getOutputQueue(
            "h264_out", maxSize=30, blocking=False
        )
        color_queue: dai.DataOutputQueue = device.getOutputQueue(
            "color_out", maxSize=30, blocking=False
        )
        nn_queue: dai.DataOutputQueue = device.getOutputQueue(
            "nn_out", maxSize=30, blocking=False
        )

        self.live_view = rh.DepthaiLiveView("Live view", "live_view", *CAM_SIZE)

        log.info("Application running")
        while rh.app_is_running():
            h264_packet: dai.ImgFrame = h264_queue.get()
            color_packet: dai.ImgFrame = color_queue.get()
            nn_packet: dai.NNData = nn_queue.get()

            text_detections = self.recognize_text(nn_packet, color_packet)

            # Filter out results with low confidence
            filtered_text_detections = self.filter_detections_below_threshold(
                text_detections, RECOGNITION_CONF_THRESHOLD
            )
            # Visualize detections with lower confidence to prevent bounding box flickering on live view
            visualization_text_detections = self.filter_detections_below_threshold(
                text_detections, VISUALIZATION_CONF_THRESHOLD
            )

            # Run search only if we detect 2 or more words
            if len(filtered_text_detections) >= 2:
                self.try_search_and_send_books_to_fe(filtered_text_detections)
            self.publish_live_view_frame(h264_packet, visualization_text_detections)

    def on_stop(self):
        super().on_stop()
        self.thread_pool_executor.shutdown(wait=True, cancel_futures=True)


if __name__ == "__main__":
    app = Application()
    app.run()
