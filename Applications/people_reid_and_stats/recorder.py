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
        self._handle_video_saving()

    def _handle_video_saving(self) -> None:
        self._local_storage = LocalStorage(subdir_path=CONFIGURATION["video_storage_location"],
                                           gib_storage_limit=CONFIGURATION["storage_space_limit"])
        video_path = self._save_video()
        self._upload_to_cloud(video_path)
        self._save_locally(video_path)

    def _save_video(self) -> Path:
        av_writer = AvWriter(path=self._local_storage.get_dir_path(),
                             name=self._record_id,
                             fourcc='h264',
                             fps=CONFIGURATION["fps"],
                             frame_shape=(IMAGE_WIDTH, IMAGE_HEIGHT))
        packets = list(self.__buffer)
        for p in packets:
            av_writer.write(p)
        av_writer.close()
        return Path(self._local_storage.get_dir_path(), self._record_id).with_suffix('.mp4')

    def _upload_to_cloud(self, video_path: Path):
        if CONFIGURATION["cloud_storage_enabled"]:
            log.info(f"Saving video on cloud")
            send_video_event(video=video_path.as_posix(), title=f"Recording {self._record_id}")

    def _save_locally(self, video_path: Path):
        self._local_storage.manage_stored_file(file_path=video_path,
                                               local_storage_enabled=CONFIGURATION["local_storage_enabled"],
                                               remove_oldest_enabled=CONFIGURATION["remove_oldest_enabled"])
