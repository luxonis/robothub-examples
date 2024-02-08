import logging as log
import threading
import time
import uuid

from collections import deque
from pathlib import Path

from robothub.events import send_video_event

from base_node import BaseNode
from depthai_sdk.recorders.video_writers import AvWriter
from messages import Person, PeopleFacesMessage
from robothub_core import CONFIGURATION
from settings import IMAGE_HEIGHT, IMAGE_WIDTH
from utilities import IntervalTimer, LocalStorage


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
                and self.__timer.event_time_elapsed(event="record",
                                                    seconds=60 * CONFIGURATION["record_frequency_minutes"])
                and CONFIGURATION["recording_enabled"])

    def __record_video(self) -> None:
        thread = threading.Thread(target=self.__record_video_thread, daemon=True, name="recording_thread")
        thread.start()

    def __record_video_thread(self):
        self._record_id = str(uuid.uuid4())
        self.__timer.update_timestamp(event=self._record_id)
        log.info(f"Recording {self._record_id}")
        while not self.__timer.event_time_elapsed(event=self._record_id,
                                                  seconds=60 * CONFIGURATION["recording_length"]):
            time.sleep(1.)
        self.__save_video()

    def __save_video(self) -> None:
        self._local_storage = LocalStorage(file_name=self._record_id, file_suffix='.mp4',
                                           subdir_path=CONFIGURATION["video_storage_location"],
                                           gib_storage_limit=CONFIGURATION["storage_space_limit"])
        av_writer = AvWriter(path=self._local_storage.get_dir_path(),
                             name=self._record_id,
                             fourcc='h264',
                             fps=CONFIGURATION["fps"],
                             frame_shape=(IMAGE_WIDTH, IMAGE_HEIGHT))
        packets = list(self.__buffer)
        for p in packets:
            av_writer.write(p)
        av_writer.close()

        self._handle_video_saving(video_path=self._local_storage.get_video_path())

    def _handle_video_saving(self, video_path: Path) -> None:
        log.info(f"Storing image remotely")
        send_video_event(video=video_path.as_posix(), title=f"Recording {self._record_id}")
        if CONFIGURATION["local_storage_enabled"]:
            log.info(f"Storing image locally")
            self._local_storage.manage_stored_video(remove_oldest_enabled=CONFIGURATION["remove_oldest_enabled"])
        else:
            video_path.unlink()
