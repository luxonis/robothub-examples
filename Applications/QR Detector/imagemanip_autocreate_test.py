# camera > 9x image manip > 9x xout

import cv2
import depthai
import numpy as np
import time

from pathlib import Path


NUMBER_OF_IMAGE_MANIPS = 9


# ---------------------
#  PIPELINE DEFINITION
# ---------------------
# pipeline object
pipeline = depthai.Pipeline()


# NODES
# ColorCamera
# https://docs.luxonis.com/projects/api/en/latest/components/nodes/color_camera/
cam = pipeline.create(depthai.node.ColorCamera)
cam.setResolution(depthai.ColorCameraProperties.SensorResolution.THE_1080_P)
cam.setPreviewSize(1920,1080)
# cam.setVideoSize(1920,1080)


# create an ImageManip node and connect camera preview to its input
def create_image_manip(crop):
    # create the node
    manip = pipeline.create(depthai.node.ImageManip)
    
    # default config values
    manip.initialConfig.setFrameType(depthai.ImgFrame.Type.BGR888p)
    manip.initialConfig.setResize(512, 288)
    step = 0.4
    xmin = crop[0]
    ymin = crop[1]
    xmax = xmin + step
    ymax = ymin + step
    manip.initialConfig.setCropRect(xmin, ymin, xmax, ymax)
    
    # input image settings
    manip.inputImage.setWaitForMessage(True)
    manip.inputImage.setBlocking(True)
    manip.inputImage.setQueueSize(1)

    return manip


def create_xout(number):
    xout_video = pipeline.create(depthai.node.XLinkOut)
    stream_name = f"stream_{number}"
    xout_video.setStreamName(stream_name)

    return xout_video



crop_vals = [(0.0, 0.0), (0.0, 0.3), (0.0, 0.6), (0.3, 0.0), (0.3, 0.3), (0.3, 0.6), (0.6, 0.0), (0.6, 0.3), (0.6, 0.6)]

for i in range(NUMBER_OF_IMAGE_MANIPS):
    im = create_image_manip(crop_vals[i])
    xout = create_xout(i)

    cam.preview.link(im.inputImage)
    # cam.video.link(im.inputImage)
    im.out.link(xout.input)





# ------------------
#  RUN THE PIPELINE
# ------------------
with depthai.Device(pipeline) as device:
    video_queues = []

    for i in range(NUMBER_OF_IMAGE_MANIPS):
        queue_name = f"stream_{i}"
        video_queues.append(device.getOutputQueue(queue_name))
    
    startTime = time.monotonic()
    counter = 0

    while True:
        counter += 1
        for i, video_queue in enumerate(video_queues):
            img_msg = video_queue.get()
            stream_name = f"stream_{i}"
            frame = img_msg.getCvFrame()
            cv2.putText(frame, "fps: {:.2f}".format(counter / (time.monotonic() - startTime)), (2, frame.shape[0] - 4), cv2.FONT_HERSHEY_TRIPLEX, 0.4, (255,255,255))
            cv2.imshow(stream_name, frame)
        
        print("FPS: {:.2f}".format(counter / (time.monotonic() - startTime)))

        
        if cv2.waitKey(1) == ord('q'):
            break