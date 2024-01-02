import cv2 as cv

from helpers import standalone_runtime

"""
App configuration
"""
# Logging level
LOGGING_LEVEL = 1  # 0 - DEBUG, 1 - INFO, 2 - WARNING, 3 - ERROR, 4 - CRITICAL

"""
Circle processing configuration
"""
# Limit history of circle presence
CIRCLE_HISTORY_LENGTH = 10  # min 2
# Percentage of circle presence to consider it as present
CIRCLE_PRESENCE_THRESHOLD = 0.5  # in %
# Percentage of circle radius allowed difference for calculating similarity
CIRCLE_RADIUS_TOLERANCE = 0.1  # in %
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

if not standalone_runtime():
    # App is running on RobotHub, so we need to get the config from its data
    from robothub_core import CONFIGURATION

    LOGGING_LEVEL_MAPPING = {
        "debug": 0,
        "info": 1,
        "warning": 2,
        "error": 3,
        "critical": 4
    }

    LOGGING_LEVEL = LOGGING_LEVEL_MAPPING.get(CONFIGURATION['logging_level'], 1)
    CIRCLE_HISTORY_LENGTH = CONFIGURATION['circle_history_length']
    CIRCLE_PRESENCE_THRESHOLD = CONFIGURATION['circle_presence_threshold']
    CIRCLE_RADIUS_TOLERANCE = CONFIGURATION['circle_radius_tolerance']
    CIRCLE_DISTANCE_TOLERANCE = CONFIGURATION['circle_distance_tolerance']
    VISIBLE_CIRCLES_STRING = CONFIGURATION['visible_circles_string']
    REMOVED_CIRCLES_STRING = CONFIGURATION['removed_circles_string']
    AVERAGE_TIME_VISIBLE_CIRCLES_STRING = CONFIGURATION['average_time_visible_circles_string']
    AVERAGE_TIME_ALL_CIRCLES_STRING = CONFIGURATION['average_time_all_circles_string']
    HOUGH_CIRCLES_DP = CONFIGURATION['hough_circles_dp']
    HOUGH_CIRCLES_MIN_DIST = CONFIGURATION['hough_circles_min_dist']
    HOUGH_CIRCLES_PARAM_1 = CONFIGURATION['hough_circles_param_1']
    HOUGH_CIRCLES_PARAM_2 = CONFIGURATION['hough_circles_param_2']
    HOUGH_CIRCLES_MAX_RADIUS = CONFIGURATION['hough_circles_max_radius']
    HOUGH_CIRCLES_MIN_RADIUS = CONFIGURATION['hough_circles_min_radius']
    OPEN_CV_MEDIAN_BLUR_KERNEL_SIZE = CONFIGURATION['open_cv_median_blur_kernel_size']
