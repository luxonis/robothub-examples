import cv2 as cv

from circle.circle_manager import CircleManager
from helpers import init_logger
from overlay.overlay_display_standalone import OverlayDisplayerStandalone
from overlay.overlay_manager import OverlayManager

VIDEO_PATH = '.media/video2.mp4'
init_logger()


def run() -> None:
    video_frames = cv.VideoCapture(VIDEO_PATH)

    circle_manager = CircleManager(OverlayManager(OverlayDisplayerStandalone()))

    while True:
        has_frames, frame = video_frames.read()

        if not has_frames:
            break

        circle_manager.refresh_circles(frame)

        cv.imshow('Output', frame)

        if cv.waitKey(1) != -1:
            break

    video_frames.release()
    cv.destroyAllWindows()


if __name__ == '__main__':

    if VIDEO_PATH == '':
        exit(1)

    run()
