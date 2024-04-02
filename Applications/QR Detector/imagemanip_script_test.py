# camera > script > image manip > xout

import cv2
import depthai
import numpy as np
import time

from pathlib import Path


NN_INPUT_SIZE_W = 512
NN_INPUT_SIZE_H = 288


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


# Script
# https://docs.luxonis.com/projects/api/en/latest/components/nodes/script/
script = pipeline.create(depthai.node.Script)
# split the image from the camera into 9 tiles, save the values to a config and send it
# to the ImageManip together with the image to handle the actual cropping and resizing

# use the version with time measurements
script.setScript("""
    import time

    NN_INPUT_SIZE_W = 512
    NN_INPUT_SIZE_H = 288
                 
    crop_vals = [(0.0, 0.0), (0.0, 0.3), (0.0, 0.6), (0.3, 0.0), (0.3, 0.3), (0.3, 0.6), (0.6, 0.0), (0.6, 0.3), (0.6, 0.6)]
    
    step = 0.4
                 
    while True:
        time_report = {}
        start = time.perf_counter()
        frame = node.io['in_preview'].get()
        time_report['img'] = time.perf_counter() - start

        start_loop = time.perf_counter()
        time_report['dets'] = []
        for val in crop_vals:
            start_det = time.perf_counter()
            xmin = val[0]
            ymin = val[1]
            xmax = xmin + step
            ymax = ymin + step

            config = ImageManipConfig()
            config.setFrameType(ImgFrame.Type.BGR888p)
            config.setCropRect(xmin, ymin, xmax, ymax)
            config.setResize(NN_INPUT_SIZE_W, NN_INPUT_SIZE_H)

            node.io['out_cfg'].send(config)
            node.io['out_frame'].send(frame)
            time_report['dets'].append(time.perf_counter() - start_det)
        time_report['det_loop'] = time.perf_counter() - start_loop

        min_, max_, sum_ = None, None, 0.
        for i, det in enumerate(time_report['dets']):
            if min_ is None or det < min_[0]:
                min_ = (det, i)
            if max_ is None or det > max_[0]:
                max_ = (det, i)
            sum_ += det
        node.warn(
            f"img: {time_report['img']:.5f}, "
            f"dets: ("
            f"loop: {time_report['det_loop']:.5f}, "
            f"avg: {sum_ / 9.:.5f}, "
            f"min: ({min_[0]:.5f}, {min_[1]})"
            f"max: ({max_[0]:.5f}, {max_[1]})"
            f")"
        )
""")


script.inputs["in_preview"].setBlocking(True)
script.inputs["in_preview"].setQueueSize(1)


# ImageManip
manip = pipeline.create(depthai.node.ImageManip)
manip.inputConfig.setWaitForMessage(True)
manip.inputConfig.setBlocking(True)  # set blocking, otherwise configs in queue might be overwritten
manip.inputConfig.setQueueSize(1)
manip.inputImage.setWaitForMessage(True)
manip.inputImage.setBlocking(True)  # set blocking, otherwise configs in queue might be overwritten
manip.inputImage.setQueueSize(1)
manip.setMaxOutputFrameSize(NN_INPUT_SIZE_W * NN_INPUT_SIZE_H * 3)


# XLinkOut (camera video)
xout_manip = pipeline.create(depthai.node.XLinkOut)
xout_manip.setStreamName("video")


# LINKS
# camera (preview) -> script
cam.preview.link(script.inputs['in_preview'])
# cam.video.link(script.inputs['in_preview'])

# script -> image manip (config)
script.outputs['out_cfg'].link(manip.inputConfig)
# script -> image manip (frame)
script.outputs['out_frame'].link(manip.inputImage)

# image manip -> host
manip.out.link(xout_manip.input)



# ------------------
#  RUN THE PIPELINE
# ------------------
with depthai.Device(pipeline) as device:
    video_queue = device.getOutputQueue("video")

    crop_vals = [(0.0, 0.0), (0.0, 0.3), (0.0, 0.6), (0.3, 0.0), (0.3, 0.3), (0.3, 0.6), (0.6, 0.0), (0.6, 0.3), (0.6, 0.6)]
    CROP_FACTOR = 0.4   # corresponds to "step" in the Script node
    NUMBER_OF_CROPPED_IMAGES = 9    # corresponds to the number of cropped images created by the Script node

    frame = None
    startTime = time.monotonic()
    counter = 0

    while True:
        counter += 1

        for i in range(NUMBER_OF_CROPPED_IMAGES):    
            frame = video_queue.get().getCvFrame()
            cv2.putText(frame, "fps: {:.2f}".format(counter / (time.monotonic() - startTime)), (2, frame.shape[0] - 4), cv2.FONT_HERSHEY_TRIPLEX, 0.4, (255,255,255))
            stream_name = f"stream_{i}"
            cv2.imshow(stream_name, frame)

        print("FPS: {:.2f}".format(counter / (time.monotonic() - startTime)))


        if cv2.waitKey(1) == ord('q'):
            break