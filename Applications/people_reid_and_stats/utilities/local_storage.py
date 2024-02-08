import os
import logging as log

from pathlib import Path


class LocalStorage:
    """ LocalStorage module needs dir_path which handles where data should be stored to
    If local storage is active id doesn't delete the file where the video is stored.
    """
    def __init__(self, file_name: str, gib_storage_limit: int, file_suffix: str,
                 storage_path=Path(f'/shared'), subdir_path="robothub-media"):
        self._dir_path = self._create_dir_path(storage_path, subdir_path)
        self._video_path = self._create_video_path(file_name, file_suffix)
        self._storage_limit = gib_storage_limit

    def get_dir_path(self) -> Path:
        return self._dir_path

    def get_video_path(self):
        return self._video_path

    def manage_stored_video(self, remove_oldest_enabled=False) -> None:
        if self._is_storage_full():
            if remove_oldest_enabled:
                log.info(f"Removing oldest image")
                self._remove_oldest_videos()
            else:
                self._video_path.unlink()
                log.info(f"Remove oldest video is disabled so the recording has been deleted")
                return
        log.info(f"Recording saved to {self._video_path}")

    def _remove_oldest_videos(self) -> None:
        while self._is_storage_full():
            files = self._dir_path.glob('*')
            oldest_file = min(files, key=lambda x: x.stat().st_ctime)
            oldest_file.unlink()
            log.info(f"Removed oldest video")

    def _is_storage_full(self) -> bool:
        # 1 GIB = 1073741824 bytes
        return self._storage_limit <= (self._calculate_dir_size(dir_path=self._dir_path) / 1073741824)

    def _create_video_path(self, file_name: str, file_suffix: str) -> Path:
        return Path(self._dir_path, file_name).with_suffix(file_suffix)

    @staticmethod
    def _calculate_dir_size(dir_path) -> int:
        for root, dirs, files in os.walk(dir_path):
            return sum(os.path.getsize(os.path.join(root, name)) for name in files)

    @staticmethod
    def _create_dir_path(file_path: Path, subdir: str) -> Path:
        subdir = subdir.lstrip(' /')
        dir_path = file_path / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
