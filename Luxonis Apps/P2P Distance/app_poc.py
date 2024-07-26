#!/usr/bin/env python3

import cv2
import numpy as np
import depthai as dai

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

    def calculate_distance(self, points, depthFrame, frame):
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
MEDIAN = dai.MedianFilter.KERNEL_5x5
SUBPIXEL = False # for long range measurement

pipeline = dai.Pipeline()

# define sources and outputs
monoLeft = pipeline.create(dai.node.MonoCamera)
monoRight = pipeline.create(dai.node.MonoCamera)
monoCams = [monoLeft, monoRight]

stereo = pipeline.create(dai.node.StereoDepth)

xoutDepth = pipeline.create(dai.node.XLinkOut)
xoutRectifLeft = pipeline.create(dai.node.XLinkOut)

xoutDepth.setStreamName("depth")
xoutRectifLeft.setStreamName("rectifiedLeft")

# properties
for monoCam in monoCams:
    monoCam.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)

stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
stereo.initialConfig.setMedianFilter(MEDIAN)
stereo.initialConfig.setConfidenceThreshold(250)
stereo.setLeftRightCheck(LR_CHECK)
stereo.setExtendedDisparity(EXTENDED)
stereo.setSubpixel(SUBPIXEL)

config = stereo.initialConfig.get()
config.postProcessing.speckleFilter.enable = True
config.postProcessing.speckleFilter.speckleRange = 1000
config.postProcessing.temporalFilter.enable = False
config.postProcessing.spatialFilter.enable = True
config.postProcessing.spatialFilter.holeFillingRadius = 2
config.postProcessing.spatialFilter.numIterations = 1
config.postProcessing.thresholdFilter.minRange = 400
config.postProcessing.thresholdFilter.maxRange = 15000
config.postProcessing.decimationFilter.decimationFactor = 1
stereo.initialConfig.set(config)

# link
monoLeft.out.link(stereo.left)
monoRight.out.link(stereo.right)
stereo.depth.link(xoutDepth.input)
stereo.rectifiedLeft.link(xoutRectifLeft.input)

# Trackers 
tracker1 = cv2.legacy.TrackerCSRT_create()
tracker2 = cv2.legacy.TrackerCSRT_create()

# Connect to device and start pipeline
with dai.Device(pipeline) as device:
    qDepth = device.getOutputQueue(name="depth", maxSize=4, blocking=False)
    qRectifLeft = device.getOutputQueue(name="rectifiedLeft", maxSize=4, blocking=False)

    distance_calculator = DistanceCalculator(hfov=71.86, image_w=640)
    point_tracker = PointTracker()
    drawer = PointDistanceDrawer(point_tracker)

    while True:
        inDepth = qDepth.get()
        depthFrame = inDepth.getFrame()

        inRectifLeft = qRectifLeft.get()
        rectifLeftFrame = cv2.cvtColor(inRectifLeft.getFrame(), cv2.COLOR_GRAY2BGR)

        cvColorMap = cv2.applyColorMap(np.arange(256, dtype=np.uint8), cv2.COLORMAP_JET)
        depthFrameColored = cv2.applyColorMap((depthFrame * (255.0 / stereo.initialConfig.getMaxDisparity())).astype(np.uint8), cvColorMap)

        cv2.setMouseCallback("rectifiedLeft", drawer.click_event, {'depthFrame': depthFrame, 'frame': rectifLeftFrame, 'distance_calculator': distance_calculator, 'point_tracker': point_tracker})
        drawer.update_distance(distance_calculator.calculate_distance(point_tracker.points, depthFrame, rectifLeftFrame))
        drawer.draw(rectifLeftFrame)
        cv2.imshow("rectifiedLeft", rectifLeftFrame)

        cv2.imshow("depth", depthFrameColored)

        key = cv2.waitKey(1)
        if key == ord('q'):
            break
        elif key == ord('c'):
            point_tracker.clear()

cv2.destroyAllWindows()
