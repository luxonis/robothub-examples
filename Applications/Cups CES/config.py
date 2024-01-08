import cv2 as cv

from helpers import standalone_runtime

"""
App configuration
"""
# Logging level
LOGGING_LEVEL = 1  # 0 - DEBUG, 1 - INFO, 2 - WARNING, 3 - ERROR, 4 - CRITICAL
FPS = 2
AUTO_EXPOSURE_ROI = "0.2,0.2,0.8,0.8"

"""
Circle processing configuration
"""
# Limit history of circle presence
CIRCLE_HISTORY_LENGTH = 10  # min 2
# Percentage of circle presence to consider it as present
CIRCLE_PRESENCE_THRESHOLD = 0.8  # in %
# Percentage of circle radius allowed difference for calculating similarity
CIRCLE_RADIUS_TOLERANCE = 0.2  # in %
# Allowed distance between circle centers for calculating similarity
CIRCLE_DISTANCE_TOLERANCE = 20  # in pixels

"""
Displayed text configuration
- {} is a placeholder for a value, don't forget to include it in the string where you want the value to be displayed
"""
# Visible circles displayed string
VISIBLE_CIRCLES_STRING = 'Cups: {}'
# Removed circles displayed string
REMOVED_CIRCLES_STRING = 'Removed cups: {}'
# Average time of visible circles displayed string
AVERAGE_TIME_VISIBLE_CIRCLES_STRING = 'Cups AVG time: {}'
# Average time of all circles displayed string
AVERAGE_TIME_ALL_CIRCLES_STRING = 'All cups AVG time: {}'

"""
OpenCV configuration
"""
# HoughCircles parameters
HOUGH_CIRCLES_DP = 1.2
HOUGH_CIRCLES_MIN_DIST = 75
HOUGH_CIRCLES_PARAM_1 = 150
HOUGH_CIRCLES_PARAM_2 = 100
HOUGH_CIRCLES_MAX_RADIUS = 0
HOUGH_CIRCLES_MIN_RADIUS = 0
# Preprocessing configuration
OPEN_CV_MEDIAN_BLUR_KERNEL_SIZE = 9
# Basic configuration
OPEN_CV_FONT = cv.FONT_HERSHEY_SIMPLEX  # standalone only
