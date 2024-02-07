import os
import logging as log

from pathlib import Path
from robothub_core import CONFIGURATION


class LocalStorage:
    """ LocalStorage module needs an implementation of save function that returns a path to stored video.
    If local storage is active id doesn't delete the file where the video is stored.
    """
    def __init__(self, record_id, save_function):
        self._dir_path = LocalStorage.__create_dir_path()
        self._record_id = record_id
        self._save_function = save_function

    def handle_video_saving(self) -> None:
        if CONFIGURATION["local_storage_enabled"]:
            self.__store_locally()
        else:
            self.__store_on_cloud()

    def __store_locally(self) -> None:
        video_path = self._save_function(name=self._record_id, dir_path=self.__create_dir_path())
        if self.__is_storage_full():
            if CONFIGURATION["remove_oldest_enabled"]:
                self.__remove_oldest_videos()
            else:
                video_path.unlink()
                log.info(f"Remove oldest video is disabled so the recording has been deleted")
                return
        log.info(f"Recording saved to {video_path}")

    def __store_on_cloud(self):
        video_path = self._save_function(name=self._record_id, dir_path=self.__create_dir_path())
        video_path.unlink()
        pass

    def __remove_oldest_videos(self) -> None:
        while self.__is_storage_full():
            files = self._dir_path.glob('*')
            oldest_file = min(files, key=lambda x: x.stat().st_ctime)
            oldest_file.unlink()
            log.info(f"Removed oldest video")

    def __is_storage_full(self) -> bool:
        return CONFIGURATION["storage_space_limit"] >= os.path.getsize(self._dir_path)

    @staticmethod
    def __create_dir_path() -> Path:
        subdir = CONFIGURATION["video_storage_location"].lstrip(' /')
        dir_path = Path(f'/shared/robothub-videos/') / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
