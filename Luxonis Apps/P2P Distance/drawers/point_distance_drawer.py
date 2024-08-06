import cv2

class PointDistanceDrawer:
    pointColor = (0, 0, 255)
    lineColor = (200, 0, 200)
    circleRadius = 2

    def __init__(self, point_tracker):
        self.point_tracker = point_tracker

    def click_event(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.point_tracker.add_point((x, y))

    def draw(self, img):
        self.draw_point(img)

    def draw_point(self, img):
        for bbox in self.point_tracker.get_boxes():
            mid = bbox[0] + bbox[2] // 2, bbox[1] + bbox[3] // 2 
            cv2.circle(img, mid, self.circleRadius, self.pointColor, -1, cv2.LINE_AA, 0)
            cv2.rectangle(img, (bbox[0], bbox[1]), 
                      (bbox[0] + bbox[2], bbox[1] + bbox[3]), 
                      self.pointColor, 1, cv2.LINE_AA, 0)

    def draw_distance_line(self, img, distance, std):
        if len(self.point_tracker.points) != 2:
            return
        p1, p2 = self.point_tracker.get_points()
        cv2.line(img, p1, p2, self.lineColor, 1, cv2.LINE_AA, 0)

        text = f"{distance:.2f} cm"
        if std != -1:
            text += f" +/- {std:.2f} cm"

        # First, draw the border in black
        cv2.putText(img, text, 
                    ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.5, 
                    (0, 0, 0), 
                    2, 
                    cv2.LINE_AA)

        # Then, draw the inner text in white
        cv2.putText(img, text, 
                    ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.5, 
                    (255, 255, 255), 
                    1, 
                    cv2.LINE_AA)

    def draw_depth_val(self, img, depthFrame):
        # draw on top of each point the depth value 
        for bbox in self.point_tracker.get_boxes():
            point = bbox[0] + bbox[2] // 2, bbox[1] + bbox[3] // 2
            depth = depthFrame[point[1], point[0]] / 10
            # broder in black
            cv2.putText(img, f"{depth:.2f} cm", 
                        (point[0], point[1]),
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.5, 
                        (0, 0, 0), 
                        2, 
                        cv2.LINE_AA)
            # inner text in white
            cv2.putText(img, f"{depth:.2f} cm", 
                        (point[0], point[1]),
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.5, 
                        (255, 255, 255), 
                        1, 
                        cv2.LINE_AA)
