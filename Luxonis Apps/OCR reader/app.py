import logging as log
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import depthai as dai
import east
import frontend_notifier
import robothub as rh
from live_view_handler import LiveViewHandler
from model import SearchResult
from ocr_reader import OcrReader
from open_library_client import OpenLibraryClient
from pipeline import CAM_SIZE, create_pipeline


class Application(rh.BaseDepthAIApplication):
    def __init__(self):
        super().__init__()
        self.thread_pool_executor = ThreadPoolExecutor(max_workers=1)

        # List of detection bboxes, that are currently being searched
        self.query_bboxes: list[list[tuple[int, int]]] = []
        self.last_successful_search = datetime.now()

        self.ocr = OcrReader()
        self.live_view_handler = LiveViewHandler(
            "Live view", "live_view", CAM_SIZE[0], CAM_SIZE[1]
        )
        self.open_library_client = OpenLibraryClient()

    @property
    def can_search(self):
        """Search can only be initiated if not currently searching,
        the last search was conducted over 3 seconds ago,
        and at least two or more words have been detected for the search query"""

        return (
            not self.open_library_client.searching
            and (datetime.now() - self.last_successful_search) > timedelta(seconds=3)
            and len(self.ocr.get_query_detections()) >= 2
        )

    def setup_pipeline(self) -> dai.Pipeline:
        """Define the pipeline using DepthAI."""

        log.info(f"App config: {rh.CONFIGURATION}")
        log.info("Creating camera pipeline")
        return create_pipeline()

    def finish_search(self, search_results: list[SearchResult]):
        frontend_notifier.send_search_results(search_results)
        self.last_successful_search = datetime.now()
        self.query_bboxes = []

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
            h264_packet: dai.ImgFrame = h264_queue.get()  # type: ignore
            color_packet: dai.ImgFrame = color_queue.get()  # type: ignore
            nn_packet: dai.NNData = nn_queue.get()  # type: ignore

            # Decode text detection
            rect_points = east.decode_east(nn_packet)

            # Text recognition
            self.ocr.set_input_data(rect_points, color_packet.getCvFrame())  # type: ignore

            if self.can_search:
                self.query_bboxes = self.ocr.get_query_bboxes()
                text_query = self.ocr.get_query_text()
                frontend_notifier.send_status_update("searching", text_query)
                self.open_library_client.search_open_library_async(
                    text_query, self.finish_search
                )

            visualization_bboxes = self.ocr.get_visualization_bboxes()
            self.live_view_handler.publish_live_view_frame(
                h264_packet.getCvFrame(),  # type: ignore
                visualization_bboxes,
                self.query_bboxes,
            )

    def on_stop(self):
        super().on_stop()
        self.open_library_client.stop()


if __name__ == "__main__":
    app = Application()
    app.run()
