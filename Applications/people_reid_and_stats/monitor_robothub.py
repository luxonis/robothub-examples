import cv2
import depthai as dai
import image_drawing as img
import logging as log
import numpy as np
import robothub_core
import time

from base_node import BaseNode
from geometry import clamp
from messages import Person, PeopleFacesMessage
from pathlib import Path
from streams import LiveView
from typing import Optional


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


class FeSlotData:
    def __init__(self, face_features, image, person_id: int):
        self.face_features = face_features
        self.image = image
        self.person_id = person_id
        self.time_stamp = time.monotonic()


class FeFaceSlots:
    image_storage_path = Path("/app/frontend/event-images/")
    fe_storage_path = Path("/event-images")
    image_storage_path.mkdir(parents=True, exist_ok=True)
    gender_to_fe_conversion = {"Man": "male", "Woman": "female"}

    def __init__(self):
        self.__memory = {}
        self.__slots: dict[int, Optional[FeSlotData]] = {1: None, 2: None, 3: None, 4: None}  # FeSlotData
        self.__save_slot_image: dict[int, bool] = {1: False, 2: False, 3: False, 4: False}
        self.__last_slot_notification = time.monotonic()

    def add_candidate(self, person: Person, image_mjpeg: dai.ImgFrame):
        if person.face_features is None:
            return
        # not a new image - old face has not changed
        if person.face_features in self.__memory:
            return
        decoded_image = decode_image_from_mjpeg(image_mjpeg_encoded=image_mjpeg.getCvFrame())
        # create image crop
        cropped_face = crop_face(frame=decoded_image, face_bbox=person.face_features.bbox)

        # reshape to 1:1
        cropped_face = reshape_image(image=cropped_face)
        self.__memory[person.face_features] = FeSlotData(face_features=person.face_features,
                                                         image=cropped_face,
                                                         person_id=person.figure.tracking_id)
        self.__delete_old_faces()

    def __delete_old_faces(self):
        to_delete = []
        now = time.monotonic()
        for face_features, image_id in self.__memory.items():
            if now - image_id.time_stamp > 60:
                to_delete.append(face_features)
        for face in to_delete:
            self.__memory.pop(face)

    def display_on_fe(self):
        # sort to get the newest faces first
        l = list(self.__memory.values())
        l.sort(key=lambda x: x.time_stamp, reverse=True)
        top_4 = l[0:4]
        for top_face in top_4:
            top_face: FeSlotData
            self.__add_face_to_slot(face=top_face)
        self.___update_saved_images()
        self.__display_slots()

    def __add_face_to_slot(self, face: FeSlotData):
        """Add new top faces to the FE slots."""
        # if id already there, add it to to the same slot
        which_is_none_idx = None
        oldest_ts = 1_000_000_000_000
        oldest_idx = None
        for idx, value in self.__slots.items():
            if value is not None and face.person_id == value.person_id:
                self.__slots[idx] = face
                self.__save_slot_image[idx] = True
                return
            # remember first empty position
            if value is None and which_is_none_idx is None:
                which_is_none_idx = idx
            # find the oldest timestamp with its idx
            if value is not None:
                if value.time_stamp < oldest_ts:
                    oldest_ts = value.time_stamp
                    oldest_idx = idx
        # if not there, add it to either empty slot or replace the oldest
        if which_is_none_idx is not None:
            self.__slots[which_is_none_idx] = face
            self.__save_slot_image[which_is_none_idx] = True
            return
        # replace oldest one
        if oldest_idx is None:
            log.error(f"This is really weird. {oldest_idx=} should exist!! Investigate. {self.__slots=} {face=}")
            return
        self.__slots[oldest_idx] = face
        self.__save_slot_image[oldest_idx] = True

    def ___update_saved_images(self):
        all_images = self.image_storage_path.glob("*.jpg")
        current_data = []
        for idx, data in self.__slots.items():
            if data is None:
                continue
            if self.__save_slot_image[idx]:
                self.__save_slot_image[idx] = False
                data: FeSlotData
                log.info(f"Writing into {self.image_storage_path}/{data.person_id}.jpg")
                cv2.imwrite((self.image_storage_path / f"{data.person_id}.jpg").as_posix(), data.image)

            current_data.append(f"{data.person_id}")

        log.debug(f"{current_data=}")
        for image in all_images:
            image: Path
            if image.stem not in current_data:
                log.info(f"Unlinking {image}")
                image.unlink()

    def __display_slots(self):
        now = time.monotonic()
        if now - self.__last_slot_notification < 1:
            return
        log.info(f"Preparing payload ...")
        payload = {"faces": {"face_1": {"img_path": "/public/event_images/face_1.jpg", "emotion": "happy", "age": 26, "gender": "male"},
                             "face_2": {"img_path": "/public/event_images/face_2.jpg", "emotion": "angry", "age": 26, "gender": "male"},
                             "face_3": {"img_path": "/public/event_images/face_3.jpg", "emotion": "neutral", "age": 26, "gender": "male"},
                             "face_4": {"img_path": "/public/event_images/face_4.jpg", "emotion": "neutral", "age": 26, "gender": "male"}
                             }}
        data = self.__slots[1]
        face_1 = {"img_path": f"{self.fe_storage_path}/{data.person_id}.jpg",
                  "emotion": f"{data.face_features.emotion}",
                  "age": data.face_features.age,
                  "gender": self.gender_to_fe_conversion[data.face_features.gender]} if data is not None else {}
        data = self.__slots[2]
        face_2 = {"img_path": f"{self.fe_storage_path}/{data.person_id}.jpg",
                  "emotion": f"{data.face_features.emotion}",
                  "age": data.face_features.age,
                  "gender": self.gender_to_fe_conversion[data.face_features.gender]} if data is not None else {}
        data = self.__slots[3]
        face_3 = {"img_path": f"{self.fe_storage_path}/{data.person_id}.jpg",
                  "emotion": f"{data.face_features.emotion}",
                  "age": data.face_features.age,
                  "gender": self.gender_to_fe_conversion[data.face_features.gender]} if data is not None else {}
        data = self.__slots[4]
        face_4 = {"img_path": f"{self.fe_storage_path}/{data.person_id}.jpg",
                  "emotion": f"{data.face_features.emotion}",
                  "age": data.face_features.age,
                  "gender": self.gender_to_fe_conversion[data.face_features.gender]} if data is not None else {}
        payload["faces"]["face_1"] = face_1
        payload["faces"]["face_2"] = face_2
        payload["faces"]["face_3"] = face_3
        payload["faces"]["face_4"] = face_4
        log.info(f"{payload=}")
        robothub_core.COMMUNICATOR.notify(key="faces", payload=payload)

    def is_in_slot(self, face: FeSlotData):
        for value in self.__slots.values():
            if value is not None and face.person_id == value.person_id:
                return True
        return False


class Monitor(BaseNode):
    def __init__(self, input_node: BaseNode):
        super().__init__()
        input_node.set_callback(self.__callback)
        self.__fe_face_slots = FeFaceSlots()
        self.__window_names = {}  # id + window name
        self.live_view = LiveView(camera_serial="1234DCS1234", unique_key="color", description="Counter App")

    def __callback(self, message: PeopleFacesMessage):
        self.__show_main_window(message=message)
        # self.__show_people_faces(message=message)

    def __show_main_window(self, message: PeopleFacesMessage) -> None:
        frame = message.image.getCvFrame()
        bboxes = []
        texts = []
        for person in message.people:
            figure = person.figure.bbox
            bboxes.append(figure)
            text = f"ID: {person.figure.tracking_id} "

            if person.face_features is not None:
                # face = person.face_features.bbox
                # img.draw_rectangle(image=frame, bottom_left=(int(face.xmin * 1920), int(face.ymax * 1080)),
                #                    top_right=(int(face.xmax * 1920), int(face.ymin * 1080)), color=(0, 255, 255))
                text += f"{person.face_features.gender} {person.face_features.age} {emotion_to_emoji(person.face_features.emotion)}"
                # position = (figure.xmin + figure.xmax) // 2, figure.ymin
                # frame = img.draw_smiley(frame=frame, position=position, smiley=emotion_to_emoji(person.face_features.emotion))

            texts.append((text, (figure.xmin + 5, figure.ymax - 5)))

        self.live_view.set_bboxes(bboxes=bboxes)
        self.live_view.set_texts(texts=texts)
        self.live_view.publish(image_h264=frame)
        self.__show_people_faces(message=message)

    def __show_people_faces(self, message: PeopleFacesMessage) -> None:
        for person in message.people:
            self.__fe_face_slots.add_candidate(person, message.image_mjpeg)
        self.__fe_face_slots.display_on_fe()


def decode_image_from_mjpeg(image_mjpeg_encoded) -> np.ndarray:
    """Decode mjpeg image to BGR raw."""
    image_bgr = cv2.imdecode(image_mjpeg_encoded, cv2.IMREAD_COLOR)
    return image_bgr


def encode_image_to_mjpeg(image, mjpeg_quality=98):
    _, image = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), mjpeg_quality])
    return image


def crop_face(frame, face_bbox):
    bbox = face_bbox
    padding = 100
    new_ymin = clamp(bbox.ymin - padding, 0, 1080)
    new_ymax = clamp(bbox.ymax + padding, 0, 1080)
    new_xmin = clamp(bbox.xmin - padding, 0, 1920)
    new_xmax = clamp(bbox.xmax + padding, 0, 1920)
    cropped_face = frame[new_ymin:new_ymax, new_xmin:new_xmax]
    return cropped_face


def reshape_image(image: np.ndarray):
    height, width = image.shape[:2]
    # Determine the longer side and calculate the size of the black bars
    if height > width:
        diff = height - width
        top = bottom = 0
        left = right = diff // 2
    else:
        diff = width - height
        left = right = 0
        top = bottom = diff // 2
    # Create a new black image with the same type as the original
    letterboxed_image = np.zeros((max(height, width), max(height, width), 3), dtype=image.dtype)
    # Copy the original image to the center of the new image
    letterboxed_image[top:top + height, left:left + width] = image
    return letterboxed_image
