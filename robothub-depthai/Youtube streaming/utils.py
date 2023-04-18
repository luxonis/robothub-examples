from typing import List

def make_command(key: str) -> List[str]:

    HLS_URL = f"https://a.upload.youtube.com/http_upload_hls?cid={key}&copy=0&file=stream.m3u8"

    hls_command = [ "ffmpeg",
                    '-hide_banner',
                    "-fflags", "+genpts",
                    '-loglevel', 'info',
                    '-use_wallclock_as_timestamps', 'true',
                    '-thread_queue_size', '512',
                    "-i", "-",
                    "-f", "lavfi",
                    '-thread_queue_size', '512',
                    "-i", "anullsrc",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-f", "hls",
                    "-hls_time", "2",
                    "-hls_list_size", "4",
                    "-http_persistent", "1",
                    "-method", "PUT",
                    HLS_URL ]

    return hls_command

