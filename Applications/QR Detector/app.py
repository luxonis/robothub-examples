import cv2
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
CONFIDENCE_THRESHOLD = 0.2
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

            bboxes = []
            confidences = []
            wh = (self.detection_view.frame_width, self.detection_view.frame_height)

            # If any codes were detected, display the image, highlight the codes with rectangles,
            # display the decoded text (if available) above the highlighting rectangle,
            # and print the relevant info to the output.
            # Note: the highlighted rectangles include an (additional) border necessary for code decoding.
            # If no codes were detected, just display the image.

            for i in range(NUMBER_OF_CROPPED_IMAGES):
                # get the corresponding detections
                detections = nnQueue.get().detections

                for detection in detections:
                    # transform the bounding box from the detections space <0..1> to the yolo frame space
                    bbox_detection = (detection.xmin, detection.ymin, detection.xmax, detection.ymax)
                    bbox_yolo_frame = transform_coords(np.array([1,1]), np.array([NN_INPUT_SIZE_W,NN_INPUT_SIZE_H]), bbox_detection)

                    # transform the bounding box from the yolo frame space to the coordinates in the original image
                    bbox = transform_coords(np.array([NN_INPUT_SIZE_W,NN_INPUT_SIZE_H]), wh_from_frame(wh, CROP_FACTOR), bbox_yolo_frame, wh_from_frame(wh, crop_vals[i]))
                    bboxes.append(bbox.tolist())
                    confidences.append(detection.confidence)
                    
            confidence_threshold = CONFIDENCE_THRESHOLD     # generally should match yolo's confidence_threshold
            overlap_threshold = 0.01
            nmsboxes = [(bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1]) for bbox in bboxes]
            indices = cv2.dnn.NMSBoxes(nmsboxes, confidences, confidence_threshold, overlap_threshold)

            self.detection_view.publish(h264_frame=rgb_h264_frame.getFrame())

            # display and print info about each resulting code and try to decode it. 
            # If successful, display and print the decoded text as well.
            for index in indices:
                bbox = bboxes[index]
                self.detection_view.add_rectangle((bbox[0], bbox[1], bbox[2], bbox[3]), '')
                print(bbox[0], bbox[1], bbox[2], bbox[3])
                # cv2.putText(frame, f"{int(confidences[index] * 100)}%", (bbox[0] + 10, bbox[1] + 40), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color_red)

            time.sleep(0.01)


if __name__ == "__main__":
    app = Application()
    app.run()
