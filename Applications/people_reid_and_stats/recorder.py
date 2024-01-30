import av
import logging as log
import threading
import time
import uuid

from collections import deque
from pathlib import Path

from base_node import BaseNode
from depthai_sdk.recorders.video_writers import AvWriter
from messages import Person, PeopleFacesMessage
from robothub.events import send_video_event
from robothub_core import CONFIGURATION
from settings import IMAGE_HEIGHT, IMAGE_WIDTH
from utilities import IntervalTimer


class Recorder(BaseNode):

    def __init__(self, input_node: BaseNode):
        super().__init__()
        input_node.set_callback(self.__callback)
        self.__timer = IntervalTimer()
        self.__buffer = deque(maxlen=CONFIGURATION["fps"] * 60)

    def __callback(self, message: PeopleFacesMessage):
        self.__buffer.append(message.image)
        for person in message.people:
            person: Person
            if self.__should_record(person):
                self.__timer.update_timestamp("record")
                self.__record_video()
                return

    def __should_record(self, person: Person) -> bool:
        return (person.face_features is not None
                and self.__timer.event_time_elapsed(event="record", seconds=60 * CONFIGURATION["record_frequency_minutes"])
                and CONFIGURATION["recording_enabled"])

    def __record_video(self) -> None:
        thread = threading.Thread(target=self.__record_video_thread, daemon=True, name="recording_thread")
        thread.start()

    def __record_video_thread(self):
        record_id = str(uuid.uuid4())
        self.__timer.update_timestamp(event=record_id)
        log.info(f"Recording {record_id}")
        while not self.__timer.event_time_elapsed(event=record_id, seconds=60 * CONFIGURATION["recording_length"]):
            time.sleep(1.)
        video_path = self.__save_video(name=record_id)
        send_video_event(video=video_path.as_posix(), title=f"Recording {record_id}")
        video_path.unlink()

    def __save_video(self, name: str) -> Path:
        dir_path = Path(f'/shared/robothub-videos/')
        dir_path.mkdir(parents=True, exist_ok=True)
        av_writer = AvWriter(path=Path(dir_path),
                             name=name,
                             fourcc='h264',
                             fps=CONFIGURATION["fps"],
                             frame_shape=(IMAGE_WIDTH, IMAGE_HEIGHT))
        packets = list(self.__buffer)
        for p in packets:
            av_writer.write(p)

        av_writer.close()
        video_path = Path(dir_path, name).with_suffix('.mp4')
        log.info(f"Recording saved to {video_path}")
        return video_path
