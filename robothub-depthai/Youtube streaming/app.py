import robothub_depthai
import subprocess as sp
import utils
import robothub

from depthai_sdk.classes.packets import FramePacket


class StreamingApp(robothub_depthai.RobotHubApplication):
    
    config = robothub.CONFIGURATION
    bitrate: int = config["bitrate"]
    fps: int = config["fps"]
    key: str = config["streaming_key"]
    proc: sp.Popen = None

    def setup_pipeline(self, camera: robothub_depthai.HubCamera):
        oak = camera.oak_camera

        cam_component = oak.create_camera(source="color", resolution="1080p", fps=self.fps, encode='h264')

        def on_update(packet: FramePacket):
            frame_data = packet.imgFrame.getData()
            self.proc.stdin.write(frame_data)

        oak.callback(cam_component.out.encoded, on_update)

        oak.build()

        cam_component.config_encoder_h26x(bitrate_kbps=self.bitrate)

    def on_start(self):
        command = utils.make_command(self.key)
        if self.proc: self.proc.kill()
        self.proc = sp.Popen(command, stdin=sp.PIPE, stderr=None)
	
	# NOTE: this ensures that we try to stream from 1 camera only,
	# feel free to remake it if there is some better way
	self.setup_pipeline(self.unbooted_cameras[0])

    def on_stop(self):
        if self.proc: self.proc.kill()
        print("STREAM TERMINATED")

        super().on_stop()

