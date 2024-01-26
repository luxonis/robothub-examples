import os
import signal
import subprocess
from robothub import BaseApplication

class Application(BaseApplication):
    def __init__(self):
        super().__init__()
        self.ros_proc = None
    def on_start(self):
        env = dict(os.environ)
        self.ros_proc = subprocess.Popen(
            "bash -c 'chmod +x /app/start_ros.sh ; /app/start_ros.sh'", shell=True, env=env, preexec_fn=os.setsid
        )
    def on_stop(self):
        if self.ros_proc is not None:
            pgid = os.getpgid(self.ros_proc.pid)
            os.killpg(pgid, signal.SIGTERM)
    