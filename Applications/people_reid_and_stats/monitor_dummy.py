
import depthai as dai

from base_node import BaseNode
from geometry import clamp
from messages import Person, PeopleFacesMessage
from streams import LiveView


class Smileys:
    HAPPY = "\U0001F601"
    SAD = "\U0001F641"
    NEUTRAL = "\U0001F610"
    SURPRISE = "\U0001F632"
    ANGRY = "\U0001F620"


def emotion_to_emoji(emotion: str) -> str:
    # cases for strings
    if emotion == "happy":
        return Smileys.HAPPY
    elif emotion == "sad":
        return Smileys.SAD
    elif emotion == "neutral":
        return Smileys.NEUTRAL
    elif emotion == "surprise":
        return Smileys.SURPRISE
    elif emotion == "anger":
        return Smileys.ANGRY


class Monitor(BaseNode):
    def __init__(self):
        super().__init__()
        self.__window_names = {}  # id + window name
        self.live_view = LiveView(camera_serial="1234DCS1234", unique_key="color", description="Counter App")

    def monitor_cb(self, frame):
        self.__show_main_window(frame=frame)
        # self.__show_people_faces(message=message)

    def __show_main_window(self, frame: dai.ImgFrame) -> None:

        self.live_view.publish(image_h264=frame.getCvFrame())
