import numpy as np 
from collections import deque
import cv2

class DistanceCalculator:
    hfov = None
    image_w = None

    def __init__(self, hfov, image_w, k_matrix, maxlen=50):
        self.hfov = hfov
        self.image_w = image_w
        self.distances = deque(maxlen=maxlen)
        self.show_confidence_interval = True
        self.k_matrix = k_matrix
    
    def toggle_confidence_interval(self):
        self.show_confidence_interval = not self.show_confidence_interval

    def clear_distances(self):
        self.distances.clear()

    def convert_pixel_to_cm(self, z):
        view_width_cm = 2 * z * np.tan(np.radians(self.hfov / 2))
        return view_width_cm / self.image_w

    def add_distance(self, distance):
        if distance != -1 and self.show_confidence_interval:
            self.distances.append(distance)

    def get_average_distance(self):
        if len(self.distances) == 0 or not self.show_confidence_interval:
            return -1
        return np.mean(self.distances)

    def get_confidence_interval(self):
        if len(self.distances) == 0 or not self.show_confidence_interval:
            return -1, -1
        return self.get_average_distance(), np.std(self.distances)

    # this is not robust enough
    def calculate_distance(self, points, depthFrame):
        if len(points) != 2:
            return -1, -1
        x1, y1 = points[0]['bbox'][0] + points[0]['bbox'][2] // 2, points[0]['bbox'][1] + points[0]['bbox'][3] // 2
        x2, y2 = points[1]['bbox'][0] + points[1]['bbox'][2] // 2, points[1]['bbox'][1] + points[1]['bbox'][3] // 2

        # convert depth from mm to cm
        depth1 = depthFrame[y1, x1] / 10 
        depth2 = depthFrame[y2, x2] / 10
        
        if depth1 == 0 or depth2 == 0:
            return -1, -1
            
        cm_per_px_p1 = self.convert_pixel_to_cm(depth1)
        cm_per_px_p2 = self.convert_pixel_to_cm(depth2)

        x1_cm = x1 * cm_per_px_p1
        y1_cm = y1 * cm_per_px_p1
        x2_cm = x2 * cm_per_px_p2
        y2_cm = y2 * cm_per_px_p2

        # 3D Euclidean distance 
        dist = np.sqrt((x2_cm - x1_cm)**2 + (y2_cm - y1_cm)**2 + (depth2 - depth1)**2)
        self.add_distance(dist)
        
        # print("x1: ", x1_cm, "cm")
        # print("y1: ", y1_cm, "cm")
        # print("Depth1: ", depth1, "cm")
        # print("x2: ", x2_cm, "cm")
        # print("y2: ", y2_cm, "cm")
        # print("Depth2: ", depth2, "cm")
        # print("Distance: ", dist, "cm")
        # print("--------------------------------------")
        # print()

        if self.show_confidence_interval:
            return self.get_confidence_interval()

        return dist, -1

    def calculate_distance_with_k(self, points, depthFrame):
        # calculate distance using the camera matrix 
        if len(points) != 2:
            return -1, -1
        x1, y1 = points[0]['bbox'][0] + points[0]['bbox'][2] // 2, points[0]['bbox'][1] + points[0]['bbox'][3] // 2 
        x2, y2 = points[1]['bbox'][0] + points[1]['bbox'][2] // 2, points[1]['bbox'][1] + points[1]['bbox'][3] // 2 
         
        u_1 = np.array([x1, y1, 1]) 
        u_2 = np.array([x2, y2, 1]) 
        depth1 = depthFrame[y1, x1] / 10
        depth2 = depthFrame[y2, x2] / 10

        # inverse intrinsic matrix 
        k_inv = np.linalg.inv(self.k_matrix)
        # find the vector p1 and p2 in 3D space
        p1 = np.dot(k_inv, u_1) * depth1 
        p2 = np.dot(k_inv, u_2) * depth2 

        # 3D Euclidean distance 
        dist = np.linalg.norm(p1 - p2)
        self.add_distance(dist)

        if self.show_confidence_interval:
            return self.get_confidence_interval()

        return dist, -1
