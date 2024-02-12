import os
import logging as log

from pathlib import Path


class LocalStorage:
    """ Local storage handles 1 directory specified in dir_path, which cannot store more than GIB of data than
    gib_storage_limit. You can manipulate and reassign file_path in case you would want to store more images.
    """
    def __init__(self, file_name: str, gib_storage_limit: int, file_suffix: str,
                 storage_path=Path(f'/shared'), subdir_path="robothub-media"):
        self._dir_path = self._create_dir_path(storage_path, subdir_path)
        self.file_path = self._create_file_path(file_name, file_suffix)
        self._storage_limit = gib_storage_limit

    def get_dir_path(self) -> Path:
        return self._dir_path

    def manage_stored_file(self, local_storage_enabled: bool, remove_oldest_enabled=False) -> None:
        if local_storage_enabled:
            log.info(f"Storing image locally")
            if self._is_storage_full():
                if remove_oldest_enabled:
                    log.info(f"Removing oldest image")
                    self._remove_oldest_files()
                else:
                    self.file_path.unlink()
                    log.info(f"Remove oldest video is disabled so the recording has been deleted")
                    return
            log.info(f"Recording saved to {self.file_path}")
        else:
            self.file_path.unlink()

    def _remove_oldest_files(self) -> None:
        while self._is_storage_full():
            files = self._dir_path.glob('*')
            oldest_file = min(files, key=lambda x: x.stat().st_ctime)
            oldest_file.unlink()
            log.info(f"Removed oldest video")

    def _is_storage_full(self) -> bool:
        # 1 GIB = 1073741824 bytes
        return self._storage_limit <= (self._calculate_dir_size(dir_path=self._dir_path) / 1073741824)

    def _create_file_path(self, file_name: str, file_suffix: str) -> Path:
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
