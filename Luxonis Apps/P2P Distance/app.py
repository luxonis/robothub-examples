#!/usr/bin/env python3

import cv2
import numpy as np
import depthai as dai
from datetime import timedelta
from datetime import datetime
import time

from drawers.point_distance_drawer import PointDistanceDrawer
from drawers.status_bar_drawer import StatusBarDrawer
from point_tracker import PointTracker
from distance_calculator import DistanceCalculator
from logging.logger import Logger

cv2.namedWindow("main", cv2.WINDOW_NORMAL)

LR_CHECK = True
EXTENDED = False # extended disparity for lowering minimal distance for depth calculation
MEDIAN = dai.MedianFilter.KERNEL_5x5
SUBPIXEL = True # for long range measurement
fps = 60
downscaleColor = True
rgbWeight = 1
depthWeight = 0
zeroDepthWeight = 0

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
stereo.initialConfig.setConfidenceThreshold(200)
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
    zeroDepthWeight = value*5 / 100

# Connect to device and start pipeline
with device:
    device.startPipeline(pipeline)
    # device.setIrLaserDotProjectorIntensity(1.0)

    qMain = device.getOutputQueue(name="main", maxSize=10, blocking=False)

    calibration = device.readCalibration()
    K_RGB = calibration.getCameraIntrinsics(dai.CameraBoardSocket.CAM_A, dai.Size2f(1280, 720))
    distance_calculator = DistanceCalculator(np.array(K_RGB))
    
    point_tracker = PointTracker()
    points_drawer = PointDistanceDrawer(point_tracker)
    status_drawer = StatusBarDrawer(textColor=(255, 255, 255), borderColor=(0, 0, 0), x=10, y=20)
    
    logger = Logger()
    # log info like date, time, camera, modes, fps, etc
    # logger.log("info", f"Date: {datetime.now().strftime('%d.%m.%Y')}")
    # logger.log("info", "Position of tested object: approximately in the middle of the frame.")
    # logger.log("info", f"Time: {datetime.now().strftime('%H:%M:%S')}")
    # logger.log("info", f"Camera: OAK-D S2")
    # logger.log("info", f"FPS: {fps}")
    # logger.log("info", f"LR_CHECK: {LR_CHECK}")
    # logger.log("info", f"EXTENDED: {EXTENDED}")
    # logger.log("info", f"MEDIAN: {MEDIAN}")
    # logger.log("info", f"SUBPIXEL: {SUBPIXEL}")
    # logger.log("info", f"downscaleColor: {downscaleColor}")
    # logger.log("info", f"Mono Resolution: 400P")
    # logger.log("info", f"Color Resolution: 1080P")
    # logger.log("info", "Stereo Depth Preset: HIGH_DENSITY")
    # logger.log("info", f"Postprocessing:")
    # logger.log("info", f"  speckleFilter: {config.postProcessing.speckleFilter.enable}")
    # logger.log("info", f"  speckleRange: {config.postProcessing.speckleFilter.speckleRange}")
    # logger.log("info", f"  temporalFilter: {config.postProcessing.temporalFilter.enable}")
    # logger.log("info", f"  spatialFilter: {config.postProcessing.spatialFilter.enable}")
    # logger.log("info", f"  holeFillingRadius: {config.postProcessing.spatialFilter.holeFillingRadius}")
    # logger.log("info", f"  numIterations: {config.postProcessing.spatialFilter.numIterations}")
    # logger.log("info", f"  minRange: {config.postProcessing.thresholdFilter.minRange}")
    # logger.log("info", f"  maxRange: {config.postProcessing.thresholdFilter.maxRange}")
    # logger.log("info", f"  decimationFactor: {config.postProcessing.decimationFilter.decimationFactor}")

    status_drawer.drawTrackBar("Zero Depth Weight", 0, 20, updateZeroDepthWeight)

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

        dist, std = distance_calculator.calculate_distance(point_tracker.points, deepFrame)
        if len(point_tracker.points) == 2 and dist != -1:
            # points = point_tracker.get_points()
            # z1 = deepFrame[points[0][1], points[0][0]] / 10
            # z2 = deepFrame[points[1][1], points[1][0]] / 10 
            z1 = 800
            z2 = 800
            
            logger.log_distance(z1, z2, dist, actual_distance=34.1, mode=point_tracker.mode['name'])

        points_drawer.draw(blended)
        points_drawer.draw_distance_line(blended, dist, std)
        points_drawer.draw_depth_val(blended, deepFrame)

        # draw status bar
        status_drawer.drawText(blended, f"Mode: {point_tracker.mode['name']}", line=0)
        status_drawer.drawText(blended, "Confidence Interval: ", distance_calculator.show_confidence_interval, line=1)
        status_drawer.drawText(blended, f"Logging: {logger.logging}", line=2)

        cv2.imshow("main", blended)

        key = cv2.waitKey(1)
        if key == ord('q'):
            break
        elif key == ord('c'):
            point_tracker.clear()
            distance_calculator.clear_distances()
        elif key == ord('i'):
            if point_tracker.mode['tracking'] == 2:
                distance_calculator.clear_distances()
                distance_calculator.toggle_confidence_interval()
        # change mode 1,2 ,3 
        elif key == ord('1'):
            point_tracker.set_mode(1)
            distance_calculator.clear_distances()
        elif key == ord('2'):
            point_tracker.set_mode(2)
            distance_calculator.clear_distances()
            distance_calculator.show_confidence_interval = False
        elif key == ord('3'):
            point_tracker.set_mode(3)
            distance_calculator.clear_distances()
            distance_calculator.show_confidence_interval = False
        elif key == ord('l'):
            time.sleep(5) 
            logger.toggle_logging()
        

cv2.destroyAllWindows()
