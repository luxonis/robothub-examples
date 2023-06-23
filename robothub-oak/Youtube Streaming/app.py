import robothub
import robothub_oak
from robothub_oak.manager import DEVICE_MANAGER
# Auxiliary functions for generating a streaming command
import utils 
# Library for launching new applications or commands in your operating system
import subprocess as sp 
from robothub_oak.packets import HubPacket


# Defining the Application class, which inherits from RobotHubApplication in robothub
class Application(robothub.RobotHubApplication): 
    def on_update(self, packet: HubPacket):
        # Callback function when receiving a new frame from the camera 
        frame_data = packet.msg.getData()  # Retrieving frame data from the packet 
        self.proc.stdin.write(frame_data)  # Passing frame data to the stdin of the streaming subprocess 
        self.proc.stdin.flush()  # Flushing stdin buffer

    def on_start(self):
        # Function called when the application starts

        # Initialization of subprocess variable
        self.proc = None  # Subprocess for streaming

        # Extracting streaming settings from robothub.CONFIGURATION
        self.bitrate = robothub.CONFIGURATION["bitrate"]  # Bitrate for streaming
        self.fps = robothub.CONFIGURATION["fps"]  # Frames per second for streaming
        self.key = robothub.CONFIGURATION["streaming_key"]  # Streaming key
        # Check if streaming key is valid
        if not self.key or self.key == 'placeholder':
            raise Exception("Please define a valid streaming key.")
        
        command = utils.make_command(self.key) + ['-loglevel', 'quiet']  # IF YOU WANT TO SEE LOGS FROM ffmpeg you can use this conf:
      #['-loglevel', 'quiet','-report'] or ['-loglevel', 'error'] 

        if self.proc:
            self.proc.kill()  # Terminating the current subprocess if it exists
        self.proc = sp.Popen(command, stdin=sp.PIPE, stderr=None)  # Launching a new streaming subprocess

        devices = DEVICE_MANAGER.get_all_devices()  # Retrieving a list of all connected devices
        for device in devices:  # Loop over all devices
            color = device.get_camera('color', resolution='1080p', fps=30)  # Retrieving the device's color camera
            color.add_callback(self.on_update, 'encoded')  # Adding a callback for receiving updated frames
            color.configure_encoder(h26x_bitrate_kbps=self.bitrate)  # Camera encoder configuration

            nn = device.create_neural_network('person-detection-retail-0013', color)  # Creating a neural network for person detection
            nn.stream_to_hub(name=f'NN stream {device.id}')  # Start streaming the neural network's results to the robothub

        DEVICE_MANAGER.start()  # Starting the device manager

    def on_stop(self):
        # Function called when the application stops
        DEVICE_MANAGER.stop()  # Stopping the device manager
        if hasattr(self, "proc"):  # Checking for the presence of a subprocess
            if self.proc:
                self.proc.stdin.close()  # Closing the stdin of the subprocess
                self.proc.kill()  # Terminating the subprocess
        print("STREAM TERMINATED")

