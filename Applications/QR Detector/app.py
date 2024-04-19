import time
import logging as log

### cv2 and av bug workaround - uncomment in local dev

# import cv2
# import numpy as np
#
# cv2.imshow("bugfix", np.zeros((10, 10, 3), dtype=np.uint8))
# cv2.destroyWindow("bugfix")

import depthai as dai
import robothub as rh
import numpy as np

from pipeline import create_pipeline
from helpers import transform_coords, wh_from_frame

# TODO: move to config
NUMBER_OF_CROPPED_IMAGES = 9
NN_INPUT_SIZE_W = 512
NN_INPUT_SIZE_H = 288
CROP_FACTOR = 0.4   # corresponds to "step" in the Script node
crop_vals = [(0.0, 0.0), (0.0, 0.3), (0.0, 0.6), (0.3, 0.0), (0.3, 0.3), (0.3, 0.6), (0.6, 0.0), (0.6, 0.3), (0.6, 0.6)]

class Application(rh.BaseDepthAIApplication):

    def __init__(self):
        super().__init__()
        self.detection_view = rh.DepthaiLiveView(name="detection_view", unique_key="rgb", width=1920, height=1080)

    def setup_pipeline(self) -> dai.Pipeline:
        pipeline = dai.Pipeline()
        create_pipeline(pipeline=pipeline)
        return pipeline

    def manage_device(self, device: dai.Device):
        log.info(f"DepthAi version: {dai.__version__}")
        log.info(f"Oak started. getting queues...")
        rgb_h264 = device.getOutputQueue(name="rgb_h264", maxSize=5, blocking=False)
        # rgb_mjpeg = device.getOutputQueue(name="rgb_mjpeg", maxSize=5, blocking=False)
        nnQueue = device.getOutputQueue("nn", maxSize=5, blocking=False)

        detections = []

        while rh.app_is_running:
            rgb_h264_frame: dai.ImgFrame = rgb_h264.get()
            # rgb_mjpeg_frame: dai.ImgFrame = rgb_mjpeg.get()
            frame = rgb_h264_frame.getCvFrame()

            print(f"frame: {frame}")

            bboxes = []
            confidences = []

            # If any codes were detected, display the image, highlight the codes with rectangles,
            # display the decoded text (if available) above the highlighting rectangle,
            # and print the relevant info to the output.
            # Note: the highlighted rectangles include an (additional) border necessary for code decoding.
            # If no codes were detected, just display the image.

            # process results from all cropped images
            for i in range(NUMBER_OF_CROPPED_IMAGES):
                # get the corresponding detections
                detections = nnQueue.get().detections
            
                # calculate coordinates of each detection wrt the original frame
                for detection in detections:
                    # transform the bounding box from the detections space <0..1> to the yolo frame space
                    bbox_detection = (detection.xmin, detection.ymin, detection.xmax, detection.ymax)
                    bbox_yolo_frame = transform_coords(np.array([1,1]), np.array([NN_INPUT_SIZE_W,NN_INPUT_SIZE_H]), bbox_detection)

                    # transform the bounding box from the yolo frame space to the coordinates in the original image
                    bbox = transform_coords(
                        np.array([NN_INPUT_SIZE_W,NN_INPUT_SIZE_H]),
                        wh_from_frame(frame, CROP_FACTOR),
                        bbox_yolo_frame,
                        wh_from_frame(frame, crop_vals[i])
                    )
                    
                    # save the final bounding box and confidence of the detection
                    bboxes.append(bbox.tolist())
                    confidences.append(detection.confidence)

            self.detection_view.publish(h264_frame=rgb_h264_frame.getFrame())
            time.sleep(0.01)


if __name__ == "__main__":
    app = Application()
    app.run()
