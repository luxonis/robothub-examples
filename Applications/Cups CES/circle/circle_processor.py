import cv2 as cv
import numpy as np
from typing import List, Tuple

import config


class CircleProcessor:

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        gray_image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        blurred_gray_image = cv.medianBlur(gray_image, config.OPEN_CV_MEDIAN_BLUR_KERNEL_SIZE)
        return blurred_gray_image

    def recognize_circles(self, image: np.ndarray) -> np.ndarray:
        return cv.HoughCircles(
            image=self.preprocess_image(image),
            method=cv.HOUGH_GRADIENT,
            dp=config.HOUGH_CIRCLES_DP,
            minDist=config.HOUGH_CIRCLES_MIN_DIST,
            param1=config.HOUGH_CIRCLES_PARAM_1,
            param2=config.HOUGH_CIRCLES_PARAM_2,
            maxRadius=config.HOUGH_CIRCLES_MAX_RADIUS,
            minRadius=config.HOUGH_CIRCLES_MIN_RADIUS
        )

    def remove_circles_outside_image_bounds(self, circles: np.ndarray, image: np.ndarray) -> List[Tuple[int, int, int]]:
        height, width = image.shape[:2]

        circles = [] if circles is None else np.round(circles[0, :]).astype('int')

        def is_circle_inside_bounds(circle):
            center_x, center_y = (circle[0], circle[1])
            radius = circle[2]

            return (
                0 <= center_x - radius < width
                and 0 <= center_x + radius < width
                and 0 <= center_y - radius < height
                and 0 <= center_y + radius < height
            )

        return [circle for circle in circles if is_circle_inside_bounds(circle)]

    def process_circles(self, image: np.ndarray) -> List[Tuple[int, int, int]]:
        circles = self.remove_circles_outside_image_bounds(
            self.recognize_circles(image), image
        )

        return [] if circles is None else circles
