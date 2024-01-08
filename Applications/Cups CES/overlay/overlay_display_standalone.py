import cv2
import time
import numpy as np

import config
from circle.circle import Circle
from circle.circle_helper import format_seconds_into_timer
from circle.circle_list import CircleList
from overlay.overlay_display import OverlayDisplayer


class OverlayDisplayerStandalone(OverlayDisplayer):

    def display_circles(self, image: np.ndarray, circles: CircleList) -> None:
        [self.process_circle(image, circle) for circle in circles]

    def display_info(self, image, text) -> None:
        font_scale = 1
        thickness = 2

        text_size, _ = cv2.getTextSize(text, config.OPEN_CV_FONT, font_scale, thickness)
        line_height = text_size[1] + 10
        x, y0 = (50, text_size[1] + 30)

        # draw black background
        image = self.fill_rounded_rectangle(img=image, start_point=(35, 15), end_point=(500, 170),
                                            color=(0, 0, 0), radius=20)

        for i, line in enumerate(text.split('\n')):
            y = y0 + i * line_height
            cv2.putText(image, line, (x, y), config.OPEN_CV_FONT, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)

    def place_text_in_circle(self, x: int, y: int, text: str, image: np.ndarray) -> None:
        font_scale = 0.7
        font_thickness = 1

        text_size = cv2.getTextSize(text, config.OPEN_CV_FONT, font_scale, font_thickness)[0]
        text_position = (int(x - text_size[0] / 2), int(y + text_size[1] / 2))

        cv2.putText(image, text, text_position, config.OPEN_CV_FONT,
                    font_scale, (255, 255, 255), font_thickness, cv2.LINE_AA)

    def process_circle(self, image: np.ndarray, circle: Circle) -> None:
        (x, y), r = circle.center_coordinates, circle.radius
        cv2.circle(image, (x, y), r, (0, 255, 0), 4)

        text = (f"{circle.circle_id + ' ' if config.LOGGING_LEVEL == 0 else ''}"
                f"{format_seconds_into_timer(time.time() - circle.appeared_at)}")

        self.place_text_in_circle(x, y, text, image)

    def draw_rounded_rectangle(self, img, start_point, end_point, color, thickness, radius):
        """Draws a rectangle with rounded corners"""
        top_left = start_point
        bottom_right = end_point

        # Extract coordinates
        top_left_x, top_left_y = top_left
        bottom_right_x, bottom_right_y = bottom_right

        # Draw the four sides
        img = cv2.line(img, (top_left_x + radius, top_left_y), (bottom_right_x - radius, top_left_y), color, thickness)
        img = cv2.line(img, (top_left_x + radius, bottom_right_y), (bottom_right_x - radius, bottom_right_y), color, thickness)
        img = cv2.line(img, (top_left_x, top_left_y + radius), (top_left_x, bottom_right_y - radius), color, thickness)
        img = cv2.line(img, (bottom_right_x, top_left_y + radius), (bottom_right_x, bottom_right_y - radius), color, thickness)

        # Draw the four corners
        img = cv2.ellipse(img, (top_left_x + radius, top_left_y + radius), (radius, radius), 180, 0, 90, color, thickness)
        img = cv2.ellipse(img, (bottom_right_x - radius, top_left_y + radius), (radius, radius), 270, 0, 90, color, thickness)
        img = cv2.ellipse(img, (bottom_right_x - radius, bottom_right_y - radius), (radius, radius), 0, 0, 90, color, thickness)
        img = cv2.ellipse(img, (top_left_x + radius, bottom_right_y - radius), (radius, radius), 90, 0, 90, color, thickness)

        return img

    def fill_rounded_rectangle(self, img, start_point, end_point, color, radius):
        """Draws and fills a rectangle with rounded corners"""
        top_left = start_point
        bottom_right = end_point

        # Extract coordinates
        top_left_x, top_left_y = top_left
        bottom_right_x, bottom_right_y = bottom_right

        # Draw and fill the central rectangle
        center_rect_start = (top_left_x, top_left_y + radius)
        center_rect_end = (bottom_right_x, bottom_right_y - radius)
        img = cv2.rectangle(img, center_rect_start, center_rect_end, color, -1)

        # Draw and fill the top and bottom rectangles
        top_rect_start = (top_left_x + radius, top_left_y)
        top_rect_end = (bottom_right_x - radius, top_left_y + radius)
        img = cv2.rectangle(img, top_rect_start, top_rect_end, color, -1)

        bottom_rect_start = (top_left_x + radius, bottom_right_y - radius)
        bottom_rect_end = (bottom_right_x - radius, bottom_right_y)
        img = cv2.rectangle(img, bottom_rect_start, bottom_rect_end, color, -1)

        # Fill the four corners with circles
        img = cv2.circle(img, (top_left_x + radius, top_left_y + radius), radius, color, -1)
        img = cv2.circle(img, (bottom_right_x - radius, top_left_y + radius), radius, color, -1)
        img = cv2.circle(img, (bottom_right_x - radius, bottom_right_y - radius), radius, color, -1)
        img = cv2.circle(img, (top_left_x + radius, bottom_right_y - radius), radius, color, -1)

        return img

    def display_thermal(self, image: np.ndarray, thermal: np.ndarray, colored_thermal, circles: CircleList) -> np.ndarray:
        for circle in circles:
            center = circle.center_coordinates
            x, y = center
            radius = circle.radius

            # Create a mask for the circular area
            mask = np.zeros_like(colored_thermal, dtype=np.uint8)
            cv2.circle(mask, center, radius, 255, -1)

            # Extract the circular region of interest (ROI) from the thermal image
            thermal_roi = cv2.bitwise_and(colored_thermal, mask)
            average_temp = cv2.mean(thermal, mask=mask[:, :, 0])[0]
            self.place_text_in_circle(x, y + 25, f"{average_temp:.0f}deg", image)

            # Invert the mask to get the area outside the circle
            inverted_mask = cv2.bitwise_not(mask)

            # Retain original image data outside the circle
            outside_circle = cv2.bitwise_and(image, inverted_mask)

            # Combine the thermal data inside the circle with the original data outside
            combined_roi = cv2.add(thermal_roi, outside_circle)

            # Overlay the combined ROI onto the original image
            alpha = 0.5
            image[y - radius:y + radius, x - radius:x + radius] = cv2.addWeighted(image[y - radius:y + radius, x - radius:x + radius],
                                                                                  1 - alpha,
                                                                                  combined_roi[y - radius:y + radius, x - radius:x + radius],
                                                                                  alpha, 0)
        return image
