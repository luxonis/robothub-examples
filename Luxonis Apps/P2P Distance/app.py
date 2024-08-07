#!/usr/bin/env python3

import cv2
import numpy as np
import depthai as dai
from datetime import timedelta

from drawers.point_distance_drawer import PointDistanceDrawer
from drawers.status_bar_drawer import StatusBarDrawer
from point_tracker import PointTracker
from distance_calculator import DistanceCalculator

cv2.namedWindow("main", cv2.WINDOW_NORMAL)

LR_CHECK = True
EXTENDED = True # extended disparity for lowering minimal distance for depth calculation
MEDIAN = dai.MedianFilter.KERNEL_5x5
SUBPIXEL = False # for long range measurement
fps = 60
downscaleColor = True
rgbWeight = 1
depthWeight = 0
zeroDepthWeight = 0
hfov = 71.9
image_w = 1280 # image width in pixels

pipeline = dai.Pipeline()
device = dai.Device()

# define sources and outputs
monoLeft = pipeline.create(dai.node.MonoCamera)
monoRight = pipeline.create(dai.node.MonoCamera)
colorCam = pipeline.create(dai.node.ColorCamera)
stereo = pipeline.create(dai.node.StereoDepth)
sync = pipeline.create(dai.node.Sync)

xoutMain = pipeline.create(dai.node.XLinkOut)

xoutMain.setStreamName("main")

# properties
colorCam.setBoardSocket(dai.CameraBoardSocket.CAM_A)
colorCam.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P) 
colorCam.setFps(fps)
colorCam.setCamera('color')
if downscaleColor: colorCam.setIspScale(2, 3)

monoLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
monoLeft.setCamera('left')
monoRight.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
monoRight.setCamera('right')

stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
stereo.initialConfig.setMedianFilter(MEDIAN)
stereo.initialConfig.setConfidenceThreshold(250)
stereo.setLeftRightCheck(LR_CHECK)
stereo.setExtendedDisparity(EXTENDED)
stereo.setSubpixel(SUBPIXEL)

config = stereo.initialConfig.get()
config.postProcessing.speckleFilter.enable = False
config.postProcessing.speckleFilter.speckleRange = 50
config.postProcessing.temporalFilter.enable = True
config.postProcessing.spatialFilter.enable = True
config.postProcessing.spatialFilter.holeFillingRadius = 2
config.postProcessing.spatialFilter.numIterations = 1
config.postProcessing.thresholdFilter.minRange = 400
config.postProcessing.thresholdFilter.maxRange = 15000
config.postProcessing.decimationFilter.decimationFactor = 1
stereo.initialConfig.set(config)

stereo.setDepthAlign(dai.CameraBoardSocket.CAM_A)
sync.setSyncThreshold(timedelta(milliseconds=50))

# link
monoLeft.out.link(stereo.left)
monoRight.out.link(stereo.right)

stereo.disparity.link(sync.inputs['disparity'])
stereo.depth.link(sync.inputs['depth'])
colorCam.isp.link(sync.inputs['video'])

sync.out.link(xoutMain.input)

def updateZeroDepthWeight(value):
    global zeroDepthWeight
    zeroDepthWeight = value / 100

# Connect to device and start pipeline
with device:
    device.startPipeline(pipeline)

    qMain = device.getOutputQueue(name="main", maxSize=10, blocking=False)

    calibration = device.readCalibration()
    K_RGB = calibration.getCameraIntrinsics(dai.CameraBoardSocket.CAM_A, dai.Size2f(1280, 720))
    distance_calculator = DistanceCalculator(hfov, image_w, np.array(K_RGB))
    point_tracker = PointTracker()
    points_drawer = PointDistanceDrawer(point_tracker)
    status_drawer = StatusBarDrawer(textColor=(255, 255, 255), borderColor=(0, 0, 0), x=10, y=20)

    status_drawer.drawTrackBar("Zero Depth Weight", 0, 100, updateZeroDepthWeight)

    while True:
        msgGrp = qMain.get()
        deepFrame = None
        frames = {}
        for name, msg in msgGrp:
            frame = msg.getCvFrame()
            if name == 'disparity':
                frame = (frame * (255 / stereo.initialConfig.getMaxDisparity())).astype(np.uint8)
                frame = cv2.applyColorMap(frame, cv2.COLORMAP_JET)
            # convert all to BGR for blending
            if (frame.ndim == 2):
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            if name == 'depth':
                deepFrame = msg.getFrame()
            frames[name] = frame

        # create a zero depth map overlayed on the video frame 
        zero_depth_mask = (deepFrame == 0)
        zero_depth_mask_color = np.zeros_like(frames['video'])

        # convert to light red
        zero_depth_mask_color[zero_depth_mask] = (0, 0, 255)
        frames['video'] = cv2.addWeighted(frames['video'], 1, zero_depth_mask_color, zeroDepthWeight, 0)

        # cv2.imshow("disparity", frames['disparity'])

        blended = cv2.addWeighted(frames['disparity'], depthWeight, frames['video'], rgbWeight, 0)
        point_tracker.set_frame(blended)

        cv2.setMouseCallback("main", points_drawer.click_event)
        point_tracker.update()

        # dist, std = distance_calculator.calculate_distance(point_tracker.points, deepFrame)
        dist, std = distance_calculator.calculate_distance_with_k(point_tracker.points, deepFrame)
        points_drawer.draw(blended)
        points_drawer.draw_distance_line(blended, dist, std)
        points_drawer.draw_depth_val(blended, deepFrame)

        # draw status bar
        status_drawer.drawText(blended, "Tracking: ", point_tracker.tracking, line=0)
        status_drawer.drawText(blended, "Confidence Interval: ", distance_calculator.show_confidence_interval, line=1)

        cv2.imshow("main", blended)

        key = cv2.waitKey(1)
        if key == ord('q'):
            break
        elif key == ord('c'):
            point_tracker.clear()
            distance_calculator.clear_distances()
        elif key == ord('t'):
            point_tracker.toggle_tracking()
            distance_calculator.clear_distances()
            if not point_tracker.tracking:
                distance_calculator.show_confidence_interval = False
        elif key == ord('i'):
            if point_tracker.tracking:
                distance_calculator.clear_distances()
                distance_calculator.toggle_confidence_interval()

cv2.destroyAllWindows()
