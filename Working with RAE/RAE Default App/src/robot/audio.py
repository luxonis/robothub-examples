import os
import random

from rae_msgs.srv import PlayAudio

class AudioController:
    def __init__(self, ros_manager):
        self.ros_manager = ros_manager
        self.audio_client = self.ros_manager.create_service_client('/play_audio', PlayAudio)
        
    def play_audio_file(self, audio_file_path):
        req = PlayAudio.Request()
        req.mp3_file = audio_file_path
        res = self.ros_manager.call_async_srv('/play_audio', req)

    def honk(self):
        req = PlayAudio.Request()
        req.mp3_file = '/app/src/robot/assets/sfx/horn.mp3'
        res = self.ros_manager.call_async_srv('/play_audio', req)
    def play_random_sfx(self):
        req = PlayAudio.Request()
        dir = '/app/src/robot/assets/sfx/voices/'
        file = random.choice(os.listdir(dir))
        file_path = dir+file
        print(file_path)
        req.mp3_file = file_path
        res = self.ros_manager.call_async_srv('/play_audio', req)