import av
import cv2
import image_drawing as img
import logging as log
import threading

from base_node import BaseNode
from geometry import clamp
from messages import Person, PeopleFacesMessage


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
    codec_r = av.CodecContext.create("h264", "r")

    def __init__(self, input_node: BaseNode):
        super().__init__()
        input_node.set_callback(self.__callback)
        self.__window_names = {}  # id + window name

    def __callback(self, message: PeopleFacesMessage):
        self.__show_main_window(message=message)
        # self.__show_people_faces(message=message)

    def __show_main_window(self, message: PeopleFacesMessage) -> None:
        h264_frame = message.image.getCvFrame()
        frame = self.decode_h264_frame(frame=h264_frame)
        if frame is None:
            return
        for person in message.people:
            figure = person.figure.bbox
            img.draw_rectangle(image=frame, bottom_left=(figure.xmin, figure.ymax),
                               top_right=(figure.xmax, figure.ymin), color=(255, 0, 255))
            text = f"ID: {person.figure.tracking_id} "

            if person.face_features is not None:
                # face = person.face_features.bbox
                # img.draw_rectangle(image=frame, bottom_left=(int(face.xmin * 1920), int(face.ymax * 1080)),
                #                    top_right=(int(face.xmax * 1920), int(face.ymin * 1080)), color=(0, 255, 255))
                text += f"{person.face_features.gender} {person.face_features.age}"
                position = (figure.xmin + figure.xmax) // 2, figure.ymin
                frame = img.draw_smiley(frame=frame, position=position, smiley=emotion_to_emoji(person.face_features.emotion))

            img.draw_text(image=frame, text=text, bottom_left_position=(figure.xmin+5, figure.ymax-5),
                          color=(255, 255, 255), room_for_text=figure.xmax - figure.xmin)

        cv2.imshow("frame", frame)
        cv2.waitKey(1)

    def __show_people_faces(self, message: PeopleFacesMessage) -> None:
        for person in message.people:
            if person.figure.tracking_id not in self.__window_names:
                # cv2.namedWindow(f"person: {person._id}", cv2.WINDOW_NORMAL)
                self.__window_names[person.figure.tracking_id] = f"person: {person.figure.tracking_id}"
            if len(self.__window_names) > 4:
                first_key = next(iter(self.__window_names))
                window_name = self.__window_names.pop(first_key)
                cv2.destroyWindow(window_name)
            # crop face
            frame = message.image.getCvFrame()
            bbox = person.face_features.bbox
            padding = 100
            new_ymin = clamp(bbox.ymin - padding, 0, 1080)
            new_ymax = clamp(bbox.ymax + padding, 0, 1080)
            new_xmin = clamp(bbox.xmin - padding, 0, 1920)
            new_xmax = clamp(bbox.xmax + padding, 0, 1920)
            cropped_face = frame[new_ymin:new_ymax, new_xmin:new_xmax]
            width, height, *_ = cropped_face.shape
            width_step = width // 3
            img.draw_text(image=cropped_face, text=person.face_features.gender, bottom_left_position=(10, 50), color=(0, 0, 255))
            img.draw_text(image=cropped_face, text=person.face_features.emotion, bottom_left_position=(width_step, 50), color=(0, 0, 255))
            img.draw_text(image=cropped_face, text=str(person.face_features.age), bottom_left_position=(2 * width_step, 50), color=(0, 0, 255))
            cv2.imshow(self.__window_names[person.figure.tracking_id], cropped_face)

    def decode_h264_frame(self, frame):
        enc_packets = self.codec_r.parse(frame)
        if len(enc_packets) == 0:
            return None

        try:
            frames = self.codec_r.decode(enc_packets[-1])
        except Exception:
            return None

        if not frames:
            return None

        decoded_frame = frames[0].to_ndarray(format='bgr24')
        return decoded_frame
