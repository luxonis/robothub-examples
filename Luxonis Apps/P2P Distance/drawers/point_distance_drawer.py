import cv2

class PointDistanceDrawer:
    pointColor = (0, 0, 255)
    lineColor = (200, 0, 200)
    circleRadius = 2

    def __init__(self, point_tracker):
        self.point_tracker = point_tracker
        self.distance = -1

    def update_distance(self, distance):
        self.distance = distance

    def click_event(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.point_tracker.add_point(param['frame'], (x, y))

    def draw(self, img):
        self.draw_point(img)
        self.draw_line(img)

    def draw_point(self, img):
        for point in self.point_tracker.points:
            cv2.circle(img, point, self.circleRadius, self.pointColor, -1, cv2.LINE_AA, 0)

    def draw_line(self, img):
        if len(self.point_tracker.points) != 2:
            return
        p1, p2 = self.point_tracker.points
        distance = self.distance
        cv2.line(img, p1, p2, self.lineColor, 1, cv2.LINE_AA, 0)

        # First, draw the border in black
        cv2.putText(img, f"{distance:.2f} cm", 
                    ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.5, 
                    (0, 0, 0), 
                    2, 
                    cv2.LINE_AA)

        # Then, draw the inner text in white
        cv2.putText(img, f"{distance:.2f} cm", 
                    ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.5, 
                    (255, 255, 255), 
                    1, 
                    cv2.LINE_AA)
