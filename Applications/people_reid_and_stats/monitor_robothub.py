import cv2
import depthai as dai
import image_drawing as img
import logging as log
import numpy as np
import robothub as rh
import time
import uuid

from base_node import BaseNode
from geometry import clamp
from messages import Person, PeopleFacesMessage
from pathlib import Path
from streams import LiveView, OverlayData
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
    elif emotion == "angry":
        return Smileys.ANGRY


class FeSlotData:
    def __init__(self, face_features, image, person_id: int):
        self.face_features = face_features
        self.image = image
        self.person_id = person_id
        self.image_name = str(uuid.uuid4())
        self.time_stamp = time.monotonic()


class FeFaceSlots:
    image_storage_path = Path("/public/event-images/") if not rh.LOCAL_DEV else Path("images/")
    fe_storage_path = Path(f"/files/{rh.APP_INSTANCE_ID}/event-images") if not rh.LOCAL_DEV else Path("fe_storage_mock/")
    image_storage_path.mkdir(parents=True, exist_ok=True)
    gender_to_fe_conversion = {"Man": "male", "Woman": "female"}

    def __init__(self):
        self.__memory = {}
        self.__slots: dict[int, Optional[FeSlotData]] = {1: None, 2: None, 3: None}  # FeSlotData
        self.__save_slot_image: dict[FeSlotData, bool] = {}
        self.__last_slot_notification = time.monotonic()

    def add_candidate(self, person: Person, image_mjpeg: dai.ImgFrame):
        if person.face_features is None:
            return
        # not a new image - old face has not changed
        if person.face_features in self.__memory:
            # remember that this is an old image and there is no need to save it to memory again
            log.debug(f"Old face detected {self.__memory[person.face_features]}")
            return
        decoded_image = decode_image_from_mjpeg(image_mjpeg_encoded=image_mjpeg.getCvFrame())
        # create image crop
        cropped_face = crop_face(frame=decoded_image, face_bbox=person.face_features.bbox)

        # reshape to 1:1
        cropped_face = reshape_image(image=cropped_face)
        fe_slot_data = FeSlotData(face_features=person.face_features,
                                  image=cropped_face,
                                  person_id=person.figure.tracking_id)
        self.__remove_existing_old_id(fe_slot_data.person_id)
        self.__memory[person.face_features] = fe_slot_data
        log.debug(f"New face detected {fe_slot_data}")
        log.debug(f"{self.__memory=}")
        # remember that this is anew image for this face
        self.__save_slot_image[fe_slot_data] = True
        self.__delete_old_faces()

    def __remove_existing_old_id(self, id_):
        to_delete = []
        for face_features, slot_data in self.__memory.items():
            slot_data: FeSlotData
            if id_ == slot_data.person_id:
                to_delete.append(face_features)
        for d in to_delete:
            self.__memory.pop(d)

    def __delete_old_faces(self):
        to_delete = []
        now = time.monotonic()
        for face_features, image_id in self.__memory.items():
            if now - image_id.time_stamp > 60:
                to_delete.append(face_features)
        for face in to_delete:
            self.__memory.pop(face)

    def prepare_fe_data(self):
        # sort to get the newest faces first
        l = list(self.__memory.values())
        l.sort(key=lambda x: x.time_stamp, reverse=True)
        top_3 = l[0:3]
        for top_face in top_3:
            top_face: FeSlotData
            self.__add_face_to_slot(face=top_face)
        self.___update_saved_images()

    def __add_face_to_slot(self, face: FeSlotData):
        """Add new top faces to the FE slots."""
        # if id already there, add it to to the same slot
        which_is_none_idx = None
        oldest_ts = 1_000_000_000_000
        oldest_idx = None
        for idx, value in self.__slots.items():
            if value is not None and face.person_id == value.person_id:
                self.__slots[idx] = face
                log.debug(f"Add face {face} to slot {idx} because this ID has a slot")
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
            log.debug(f"Add face {face} to slot {oldest_idx} because its an empty slot")
            return
        # replace oldest one
        if oldest_idx is None:
            log.error(f"This is really weird. {oldest_idx=} should exist!! Investigate. {self.__slots=} {face=}")
            return
        self.__slots[oldest_idx] = face
        log.debug(f"Add face {face} to slot {oldest_idx} because its the oldest one")

    def ___update_saved_images(self):
        current_data = []
        log.debug(f"{self.__save_slot_image=}")
        for idx, data in self.__slots.items():
            if data is None:
                continue
            log.debug(f"{data=}")
            if data in self.__save_slot_image:
                data: FeSlotData
                write_to = (self.image_storage_path / f'{data.image_name}.jpg').as_posix()
                log.debug(f"Writing into {write_to}")
                cv2.imwrite(write_to, data.image)

            current_data.append(f"{data.image_name}")
        # clear the memory which dictates what images to save
        self.__save_slot_image.clear()

        log.debug(f"{current_data=}")
        all_images = self.image_storage_path.glob("*.jpg")
        for image in all_images:
            image: Path
            if image.stem not in current_data:
                log.debug(f"Unlinking {image}")
                image.unlink()

    def get_face_slots_payload(self):
        now = time.monotonic()
        if now - self.__last_slot_notification < 1:
            return
        payload = {"faces": {"face_1": {"img_path": "/public/event_images/face_1.jpg", "emotion": "happy", "age": 26, "gender": "male"},
                             "face_2": {"img_path": "/public/event_images/face_2.jpg", "emotion": "angry", "age": 26, "gender": "male"},
                             "face_3": {"img_path": "/public/event_images/face_3.jpg", "emotion": "neutral", "age": 26, "gender": "male"}
                             }}
        data = self.__slots[1]
        face_1 = {"img_path": f"{self.fe_storage_path}/{data.image_name}.jpg",
                  "emotion": f"{data.face_features.emotion}",
                  "age": data.face_features.age,
                  "gender": self.gender_to_fe_conversion[data.face_features.gender]} if data is not None else {}
        data = self.__slots[2]
        face_2 = {"img_path": f"{self.fe_storage_path}/{data.image_name}.jpg",
                  "emotion": f"{data.face_features.emotion}",
                  "age": data.face_features.age,
                  "gender": self.gender_to_fe_conversion[data.face_features.gender]} if data is not None else {}
        data = self.__slots[3]
        face_3 = {"img_path": f"{self.fe_storage_path}/{data.image_name}.jpg",
                  "emotion": f"{data.face_features.emotion}",
                  "age": data.face_features.age,
                  "gender": self.gender_to_fe_conversion[data.face_features.gender]} if data is not None else {}
        payload["faces"]["face_1"] = face_1
        payload["faces"]["face_2"] = face_2
        payload["faces"]["face_3"] = face_3
        log.debug(f"{payload=}")
        return payload

    def is_in_slot(self, face: FeSlotData):
        for value in self.__slots.values():
            if value is not None and face.person_id == value.person_id:
                return True
        return False


class FaceStats:
    average_age = 0
    male_percentage = 0
    female_percentage = 0
    neutral_percentage = 0
    happy_percentage = 0
    angry_percentage = 0
    surprised_percentage = 0
    sad_percentage = 0

    age: list[int] = []
    male_count: int = 0
    female_count: int = 0
    neutral_count: int = 0
    happy_count: int = 0
    angry_count: int = 0
    surprised_count: int = 0
    sad_count: int = 0

    def update_stats(self, person: Person):
        if person.face_features is None:
            return
        face_features = person.face_features
        if len(self.age) > 2000:
            self.age = self.age[-1000:]
        self.age.append(face_features.age)
        self.average_age = sum(self.age) / len(self.age)
        if face_features.gender == "Man":
            self.male_count += 1
        else:
            self.female_count += 1
        gender_sum = self.male_count + self.female_count
        self.male_percentage = self.male_count / gender_sum * 100
        self.female_percentage = self.female_count / gender_sum * 100
        if face_features.emotion == "neutral":
            self.neutral_count += 1
        elif face_features.emotion == "happy":
            self.happy_count += 1
        elif face_features.emotion == "angry":
            self.angry_count += 1
        elif face_features.emotion == "surprise":
            self.surprised_count += 1
        elif face_features.emotion == "sad":
            self.sad_count += 1
        emotions_sum = self.neutral_count + self.happy_count + self.angry_count + self.surprised_count + self.sad_count
        self.neutral_percentage = self.neutral_count / emotions_sum * 100
        self.happy_percentage = self.happy_count / emotions_sum * 100
        self.angry_percentage = self.angry_count / emotions_sum * 100
        self.surprised_percentage = self.surprised_count / emotions_sum * 100
        self.sad_percentage = self.sad_count / emotions_sum * 100

        if emotions_sum > 1_000_000:
            divisor = 100
            self.neutral_count = self.neutral_count // divisor
            self.happy_count = self.happy_count // divisor
            self.angry_count = self.angry_count // divisor
            self.surprised_count = self.surprised_count // divisor
            self.sad_count = self.sad_count // divisor

    def get_stats_text(self) -> str:

        text = (f"Avg age: {self.average_age:.1f} Males: {self.male_percentage:.1f}% Female: {self.female_percentage:.1f}%"
                f" {Smileys.HAPPY}:{self.happy_percentage:.1f}% {Smileys.NEUTRAL}:{self.neutral_percentage:.1f}% {Smileys.SURPRISE}:"
                f"{self.surprised_percentage:.1f}% {Smileys.ANGRY}:{self.angry_percentage:.1f}% {Smileys.SAD}:{self.sad_percentage:.1f}%")
        return text

    def get_fe_payload(self):
        stats = {"age": f"{self.average_age:.1f}", "males": f"{self.male_percentage:.1f}", "females": f"{self.female_percentage:.1f}",
                 "neutral": f"{self.neutral_percentage:.1f}", "happy": f"{self.happy_percentage:.1f}", "angry": f"{self.angry_percentage:.1f}",
                 "surprise": f"{self.surprised_percentage:.1f}", "sad": f"{self.sad_percentage:.1f}"}
        return stats


class Monitor(BaseNode):
    def __init__(self, input_node: BaseNode):
        super().__init__()
        input_node.set_callback(self.__callback)
        self.__fe_face_slots = FeFaceSlots()
        self.__face_stats = FaceStats()
        self.live_view = LiveView(camera_serial="1234DCS1234", unique_key="color", description="Counter App")

    def __callback(self, message: PeopleFacesMessage):
        self.__show_main_window(message=message)
        self.__update_people_faces(message=message)
        fe_stats = self.__face_stats.get_fe_payload()
        fe_face_data = self.__fe_face_slots.get_face_slots_payload()
        if fe_face_data is not None and fe_stats is not None:
            fe_payload = fe_face_data
            fe_payload["stats"] = fe_stats
            self.notify_fe(payload=fe_payload)

    def __show_main_window(self, message: PeopleFacesMessage) -> None:
        frame = message.image.getCvFrame()
        overlay_data: OverlayData = []
        texts = []
        stats = {}
        for person in message.people:
            figure = person.figure.bbox
            text = f"ID: {person.figure.tracking_id} "

            if person.face_features is not None:
                self.__face_stats.update_stats(person=person)
                # face = person.face_features.bbox
                # img.draw_rectangle(image=frame, bottom_left=(int(face.xmin * 1920), int(face.ymax * 1080)),
                #                    top_right=(int(face.xmax * 1920), int(face.ymin * 1080)), color=(0, 255, 255))
                text += f"{person.face_features.gender} {person.face_features.age} {emotion_to_emoji(person.face_features.emotion)}"
                # position = (figure.xmin + figure.xmax) // 2, figure.ymin
                # frame = img.draw_smiley(frame=frame, position=position, smiley=emotion_to_emoji(person.face_features.emotion))

            overlay_data.append((figure, text, (0, 0, 0)))
            texts.append((text, (figure.xmin + 5, figure.ymax - 5)))

        self.live_view.set_bboxes(overlay_data=overlay_data)
        self.live_view.set_texts(texts)
        # self.live_view.set_texts(texts=texts)
        self.live_view.publish(image_h264=frame)

    def notify_fe(self, payload: dict) -> None:
        rh.COMMUNICATOR.notify(key="faces", payload=payload)

    def __update_people_faces(self, message: PeopleFacesMessage) -> None:
        log.debug(f"---")
        for person in message.people:
            self.__fe_face_slots.add_candidate(person, message.image_mjpeg)
        self.__fe_face_slots.prepare_fe_data()


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
