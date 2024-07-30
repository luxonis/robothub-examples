#!/usr/bin/env python3

import cv2
import numpy as np
import depthai as dai
from datetime import timedelta

from drawers.point_distance_drawer import PointDistanceDrawer
from point_tracker import PointTracker

class DistanceCalculator:
    hfov = None
    image_w = None

    def __init__(self, hfov, image_w):
        self.hfov = hfov
        self.image_w = image_w

    def convert_pixel_to_cm(self, z):
        view_width_cm = 2 * z * np.tan(np.radians(self.hfov / 2))
        return view_width_cm / self.image_w

    def calculate_distance(self, points, depthFrame):
        if len(points) != 2:
            return -1
        x1, y1 = points[0]
        x2, y2 = points[1]
        depth1 = depthFrame[y1, x1] / 1000.0
        depth2 = depthFrame[y2, x2] / 1000.0

        if depth1 == 0 or depth2 == 0:
            # print("Invalid depth")
            return -1
            
        cm_per_px_p1 = self.convert_pixel_to_cm(depth1)
        cm_per_px_p2 = self.convert_pixel_to_cm(depth2)

        x1_cm = x1 * cm_per_px_p1
        y1_cm = y1 * cm_per_px_p1
        x2_cm = x2 * cm_per_px_p2
        y2_cm = y2 * cm_per_px_p2

        # 3D Euclidean distance 
        dist = np.sqrt((x2_cm - x1_cm)**2 + (y2_cm - y1_cm)**2 + (depth2 - depth1)**2)
        
        # Convert from m to cm 
        dist *= 100
        return dist


LR_CHECK = True
EXTENDED = False # extended disparity for lowering minimal distance for depth calculation
MEDIAN = dai.MedianFilter.KERNEL_7x7
SUBPIXEL = False # for long range measurement
fps = 30
downscaleColor = True
rgbWeight = 1
depthWeight = 0

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

# RBG needs fixed focus to properly align with depth
try:
    calibData = device.readCalibration2()
    lensPosition = calibData.getLensPosition(dai.CameraBoardSocket.CAM_A)
    if lensPosition:
        colorCam.initialControl.setManualFocus(lensPosition)
except:
    raise

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
colorCam.isp.link(sync.inputs['video'])

sync.out.link(xoutMain.input)

# Trackers 
tracker1 = cv2.legacy.TrackerCSRT_create()
tracker2 = cv2.legacy.TrackerCSRT_create()

# Connect to device and start pipeline
with device:
    device.startPipeline(pipeline)

    qMain = device.getOutputQueue(name="main", maxSize=10, blocking=False)

    distance_calculator = DistanceCalculator(hfov=71.86, image_w=640)
    point_tracker = PointTracker()
    drawer = PointDistanceDrawer(point_tracker)

    while True:
        msgGrp = qMain.get()
        deepFrame = None
        frames = {}
        for name, msg in msgGrp:
            frame = msg.getCvFrame()
            if name == 'disparity':
                deepFrame = msg.getFrame()
                frame = (frame * (255 / stereo.initialConfig.getMaxDisparity())).astype(np.uint8)
                frame = cv2.applyColorMap(frame, cv2.COLORMAP_JET)
            # convert all to BGR for blending
            if (frame.ndim == 2):
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            frames[name] = frame
        blended = cv2.addWeighted(frames['disparity'], depthWeight, frames['video'], rgbWeight, 0)
        cv2.setMouseCallback("main", drawer.click_event, {'depthFrame': frames['disparity'], 'frame': blended, 'distance_calculator': distance_calculator, 'point_tracker': point_tracker})
        point_tracker.update(frames['video'])
        drawer.update_distance(distance_calculator.calculate_distance(point_tracker.points, deepFrame))
        drawer.draw(blended)
        cv2.imshow("main", blended)

        key = cv2.waitKey(1)
        if key == ord('q'):
            break
        elif key == ord('c'):
            point_tracker.clear()

cv2.destroyAllWindows()
