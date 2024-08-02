#!/usr/bin/env python3

import cv2
import numpy as np
import depthai as dai
from datetime import timedelta

from drawers.point_distance_drawer import PointDistanceDrawer
from drawers.status_bar_drawer import StatusBarDrawer
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

        # convert depth from mm to cm
        depth1 = depthFrame[y1, x1] / 10 
        depth2 = depthFrame[y2, x2] / 10
        
        if depth1 == 0 or depth2 == 0:
            return -1
            
        cm_per_px_p1 = self.convert_pixel_to_cm(depth1)
        cm_per_px_p2 = self.convert_pixel_to_cm(depth2)

        x1_cm = x1 * cm_per_px_p1
        y1_cm = y1 * cm_per_px_p1
        x2_cm = x2 * cm_per_px_p2
        y2_cm = y2 * cm_per_px_p2

        # 3D Euclidean distance 
        dist = np.sqrt((x2_cm - x1_cm)**2 + (y2_cm - y1_cm)**2 + (depth2 - depth1)**2)
        
        # print("x1: ", x1_cm, "cm")
        # print("y1: ", y1_cm, "cm")
        # print("Depth1: ", depth1, "cm")
        # print("x2: ", x2_cm, "cm")
        # print("y2: ", y2_cm, "cm")
        # print("Depth2: ", depth2, "cm")
        # print("Distance: ", dist, "cm")
        # print("--------------------------------------")
        # print()
        
        return dist


LR_CHECK = True
EXTENDED = True # extended disparity for lowering minimal distance for depth calculation
MEDIAN = dai.MedianFilter.KERNEL_5x5
SUBPIXEL = False # for long range measurement
fps = 60
downscaleColor = True
rgbWeight = 1
depthWeight = 0
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

# Connect to device and start pipeline
with device:
    device.startPipeline(pipeline)

    qMain = device.getOutputQueue(name="main", maxSize=10, blocking=False)

    distance_calculator = DistanceCalculator(hfov, image_w)
    point_tracker = PointTracker()
    points_drawer = PointDistanceDrawer(point_tracker)
    status_drawer = StatusBarDrawer(textColor=(255, 255, 255), borderColor=(0, 0, 0), x=10, y=20)

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

        cv2.imshow("disparity", frames['disparity'])
            
        blended = cv2.addWeighted(frames['disparity'], depthWeight, frames['video'], rgbWeight, 0)
        point_tracker.set_frame(blended)
        
        cv2.setMouseCallback("main", points_drawer.click_event)
        point_tracker.update()
        points_drawer.update_distance(distance_calculator.calculate_distance(point_tracker.points, deepFrame))
        points_drawer.draw(blended)
        # draw text on top if tracking is on or off
        status_drawer.drawText(blended, "Tracking: ", point_tracker.tracking)
        cv2.imshow("main", blended)

        key = cv2.waitKey(1)
        if key == ord('q'):
            break
        elif key == ord('c'):
            point_tracker.clear()
        elif key == ord('t'):
            point_tracker.toggle_tracking()
            

cv2.destroyAllWindows()
