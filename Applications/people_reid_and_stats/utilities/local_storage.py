from pathlib import Path

from robothub.events import send_video_event
from robothub_core import CONFIGURATION


class LocalStorage:
    """ LocalStorage module needs an implementation of save function that returns a path to stored video.
    If local storage is active id doesn't delete the file where the video is stored.
    """
    @staticmethod
    def handle_video_saving(record_id: str, save_function) -> None:
        video_path = save_function(name=record_id, dir_path=LocalStorage.determine_dir_path())
        if not CONFIGURATION["local_storage_enabled"]:
            send_video_event(video=video_path.as_posix(), title=f"Recording {record_id}")
            video_path.unlink()

    @staticmethod
    def determine_dir_path() -> Path:
        if CONFIGURATION["local_storage_enabled"]:
            subdir = CONFIGURATION["video_storage_location"].lstrip(' /')
            dir_path = Path(f'/home/robothub/') / subdir
        else:
            dir_path = Path(f'/shared/robothub-videos/')
        return dir_path
