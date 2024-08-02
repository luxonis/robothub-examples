import cv2

class StatusBarDrawer:
    textColor = (255, 255, 255)
    borderColor = (0, 0, 0)
    x = 10
    y = 20
    windowName = "main"

    def __init__(self, windowName="main", textColor=(255, 255, 255), borderColor=(0, 0, 0), x=10, y=20):
        self.windowName = windowName
        self.textColor = textColor
        self.borderColor = borderColor
        self.x = x
        self.y = y

    def drawTrackBar(self, text, startingValue, endingValue, callback):
        cv2.createTrackbar(text, self.windowName, startingValue, endingValue, callback)

    def drawText(self, img, text, status=None):
        # convert bool to string
        if status == True:
            text = text + "ON"
        elif status == False:
            text = text + "OFF"

        # border
        cv2.putText(img, f"{text}", 
                    (self.x, self.y),
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.5, 
                    self.borderColor,
                    2, 
                    cv2.LINE_AA)

        # inner text
        cv2.putText(img, f"{text}", 
                    (self.x, self.y),
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.5, 
                    self.textColor,
                    1, 
                    cv2.LINE_AA)
