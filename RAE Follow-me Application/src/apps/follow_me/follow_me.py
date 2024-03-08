from time import sleep
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
import logging as log

import robothub
import time
import depthai as dai
import os
import signal

from rae_sdk.robot import Robot
from rae_sdk.robot.api.openai import OpenAIClient
from rae_msgs.msg import LEDControl, ColorPeriod
from std_msgs.msg import ColorRGBA
from src.apps.follow_me.detections import Detections, labelMap, create_detection_metadata
from src.apps.follow_me.pipeline import build_pipeline
from rae_sdk.robot.api.performance import measure_call_frequency


EXPECTED_TARGET_WIDTH = 0.4
WAIT_BEFORE_STARTING_TO_ROTATE = timedelta(seconds=2)
FOLLOWED_OBJECT_TYPES = [labelMap.index("person")]
RESOLUTION_WIDTH = 1280
RESOLUTION_HEIGHT = 800
FRONT_STREAM_NAME = "stream_front"
REAR_STREAM_NAME = "stream_back"
STREAM_NAMES = [FRONT_STREAM_NAME, REAR_STREAM_NAME]
OTHER_DIRECTIONS = {FRONT_STREAM_NAME: REAR_STREAM_NAME,
                    REAR_STREAM_NAME: FRONT_STREAM_NAME}


class AppMode(Enum):
    manual = "manual"
    follow_me = "follow_me"


class Application(robothub.RobotHubApplication):
    def __init__(self):
        super().__init__()

        self.robot = None
        self.device = None
        self.openai_client = None
        if robothub.CONFIGURATION['CHAT_API_KEY'] != 'XXX':
            self.openai_client = OpenAIClient(robothub.CONFIGURATION['CHAT_API_KEY'], robothub.CONFIGURATION['CHAT_SYSTEM_DESCRIPTION'])
        self.available_apps = []
        self.stream_handles = {}
        self.queues = {}
        self.robot_status = None
        self.latest_detections = {
            FRONT_STREAM_NAME: Detections(), REAR_STREAM_NAME: Detections()}
        self.mode = AppMode.manual
        self.folow_me_direction = None
        self.last_detection_timestamp = datetime.now()
        self.car_mode = False

    def on_start(self):
        if not robothub.DEVICES:
            log.error(
                "The default app requires an assigned device to run. "
                "Please go to RobotHub, navigate to the app's page, "
                "click the \"Reassign devices\" button and select a device."
            )
            self._stop(1)

        log.info("Starting the app...")
        log.info("Starting Robot")
        self.robot = Robot()
        log.info("Starting robothub communicator...")
        self.init_robothub_communicator()
        self.init_streams()
        log.info("Starting streams...")

    def on_stop(self):
        log.info("Stopping the app...")
        if self.robot:
            self.robot.stop()
        if self.device:
            self.device.close()
        log.info("Stopped.")

    def init_robothub_communicator(self):
        robothub.COMMUNICATOR.on_frontend(
            notification=self.on_fe_notification, request=self.on_fe_request)
        
    def init_streams(self):
        device_mxid = robothub.DEVICES[0].oak["serialNumber"]
        device_info = dai.DeviceInfo(device_mxid)
        self.device = dai.Device(device_info)
        pipeline = build_pipeline(
            dai.CameraBoardSocket.CAM_B, FRONT_STREAM_NAME, dai.CameraBoardSocket.CAM_D, REAR_STREAM_NAME
        )
        self.device.startPipeline(pipeline)
        for stream_name in STREAM_NAMES:
            self.stream_handles[stream_name] = robothub.STREAMS.create_video(
            device_mxid, stream_name, stream_name
        )

        for stream_name in STREAM_NAMES:
            self.queues[stream_name]=self.device.getOutputQueue(name=stream_name, maxSize=1, blocking=False).addCallback(self.stream_callback_rh)
            self.queues[f"{stream_name}_nn"] = self.device.getOutputQueue(name=f"{stream_name}_nn", maxSize=1, blocking=False).addCallback(
                self.control_callback_front
            )
            self.queues[f"{stream_name}_nn_pt"] = self.device.getOutputQueue(name=f"{stream_name}_nn_pt", maxSize=1, blocking=False)

    def on_fe_notification(self, session_id, unique_key, payload):
        if unique_key == "cmd_vel" and self.mode == AppMode.manual:
            self.robot.navigation.move(payload['linear'], payload['angular'])
            if self.car_mode:
                self.car_mode_leds(payload['linear'], payload['angular'])
        elif unique_key == "app_install":
            print("Received notification to app installation")
        elif unique_key == "rae_control_horn" and self.mode == AppMode.manual:
            self.robot.audio.play_audio_file("/app/src/car-horn.mp3")
        elif unique_key == "rae_control_horn" and self.mode == AppMode.follow_me:
            self.robot.audio.play_audio_file("/app/src/police-siren.mp3")
        elif unique_key == "rae_chat_describe":
            if self.openai_client:
                payload = {'brightness': 50, 'color': '#5216F2', 'effect': 'pulse', 'interval': 5}
                self.robot.led.set_leds_from_payload(payload)
                img = self.queues[f"{FRONT_STREAM_NAME}_nn_pt"].get().getCvFrame()
                descr = self.openai_client.describe_image(img)
                print(descr)
                speech_file = self.openai_client.generate_speech(descr)
                payload = {'brightness': 50, 'color': '#008000', 'effect': 'pulse', 'interval': 1}

                self.robot.led.set_leds_from_payload(payload)
                self.robot.audio.play_audio_file(speech_file)
            else:
                self.robot.display.display_text('NO API KEY', color=(0,0,255))
                log.error("No OpenAI client API KEY available in configuration!")
        elif unique_key == "rae_control_audio":
            self.robot.audio.save_recorded_sound(payload['audio'])
            self.robot.audio.play_audio_file("/app/mic_recording.wav")
        else:
            log.info(f"Unique key: {unique_key}, payload: {payload}")

        
    def on_fe_request(self, session_id, unique_key, payload):
        if unique_key == "apps_get_list":
            return self.available_apps
        elif unique_key == "robot_status":
            print("Received notification to load robot status")
            return {
                "downloadSpeed": None,
                "diskTotal": None,
                "diskUsage": None,
                "batteryCapacity": self.robot.state.state_info.battery_state.capacity,
                "mappingPaused": False,
                "mappingRunning": False,
            }
        elif unique_key == "rae_control_leds":
            self.robot.led.set_leds_from_payload(payload)
            if payload['effect'] == 'car':
                self.car_mode = True
            else:
                self.car_mode = False
        elif unique_key == "rae_control_lcd":
            self.robot.display.display_face(payload)
        elif unique_key == "change_mode":
            self.last_detection_timestamp = datetime.now()
            self.folow_me_direction = None
            try:
                self.mode = AppMode[payload.get("mode")]
                log.info(f'Robot mode set to "{self.mode.value}"')
            except KeyError:
                log.error(
                    f"Unexpected mode \"{payload.get('mode')}\" was requested, ignoring")
        else:
            log.info(f"Unique key: {unique_key}, payload: {payload}")

    def store_available_apps(self, data):
        self.available_apps = data["body"]["availableApps"]
        print(self.available_apps)

    def load_robot_info(self, data):
        self.robot_status = data["body"]
        print(self.robot_status)

    @measure_call_frequency
    def control_callback_front(self, name, msg):
        self.control_callback(name, msg)

    def control_callback_rear(self, name, msg):
        self.control_callback(name, msg)

    def control_callback(self, name, msg: dai.ImgDetections):
        direction = name[:-3]
        latest_detections = pick_detection(msg.detections)
        self.latest_detections[direction] = latest_detections
        if self.mode == AppMode.follow_me:
            self.navigate_follow_me(direction)
            
    def stream_callback_rh(self, name: str, msg: dai.ImgFrame):
        detections = self.latest_detections[name]
        metadata = create_detection_metadata(
            detections, RESOLUTION_WIDTH, RESOLUTION_HEIGHT)
        color_frame = msg.getFrame()
        timestamp = int(time.time() * 1_000)
        self.stream_handles[name].publish_video_data(
                bytes(color_frame), timestamp, metadata)

    def navigate_follow_me(self, detection_direction: str):
        current_detections = self.latest_detections[detection_direction]

        if not self.folow_me_direction and current_detections.target:
            log.info(
                f'Spotted target in direction "{detection_direction}", following')
            self.folow_me_direction = detection_direction

        if self.folow_me_direction == detection_direction and not current_detections.target:
            other_detections = self.latest_detections[detection_direction]
            if other_detections.target:
                log.info(
                    f'Lost target in direction "{self.folow_me_direction}", following in opposite direction')
                self.folow_me_direction = other_detections(detection_direction)
            else:
                log.info(
                    f'Lost target in direction "{self.folow_me_direction}", searching for new target')
                self.folow_me_direction = None
                self.last_detection_timestamp = datetime.now()

        velocity = None
        if not self.folow_me_direction:
            velocity = self.get_search_velocity()

        if self.folow_me_direction == detection_direction and current_detections.target:
            velocity = self.get_velocity_to_target(
                current_detections.target, self.folow_me_direction)

        if velocity:
            angular_velocity, linear_velocity = velocity
            self.robot.navigation.move(linear_velocity, angular_velocity)
            self.police_mode_leds()

    def get_search_velocity(self) -> Tuple[float, float]:
        linear_velocity = 0
        angular_velocity = 0
        if datetime.now() > self.last_detection_timestamp + WAIT_BEFORE_STARTING_TO_ROTATE:
            linear_velocity = 0
            angular_velocity = 1.5
        return angular_velocity, linear_velocity
    
    def car_mode_leds(self, linear_velocity, angular_velocity):
        # Set LEDs based on battery level
        # Define colors for LEDs
        colors = {
            "white": ColorPeriod(color = ColorRGBA(r=1.0, g=1.0, b=1.0, a=1.0), frequency =0.0),
            "yellow": ColorPeriod(color =ColorRGBA(r=1.0, g=1.0, b=0.0, a=1.0), frequency =8.0),
            "red": ColorPeriod(color =ColorRGBA(r=1.0, g=0.0, b=0.0, a=1.0), frequency =0.0),
            "blue": ColorPeriod(color =ColorRGBA(r=0.0, g=0.0, b=1.0, a=1.0), frequency =0.0)
        }



        # Create and publish LEDControl message for each LED
        led_msg = LEDControl()
        
        led_msg.data = [ColorPeriod(color =ColorRGBA(r=0.0, g=0.0, b=0.0, a=0.0), frequency =0.0)]*40
        for i in range(38):
            led_msg.single_led_n = 0
            led_msg.control_type = 4 
            if i < 8:
                color = "white"
                led_msg.data[i]=(colors[color])
            if i >9 and i < 14 and angular_velocity > 0.0:
                color = "yellow"
                led_msg.data[i]=(colors[color])
            if i > 20 and i < 29 and linear_velocity < 0.0:
                color = "red"
                led_msg.data[i]=(colors[color])
            if i> 34 and i < 39 and angular_velocity < 0.0:
                color = "yellow"
                led_msg.data[i]=(colors[color])

        self.robot.led.set_leds_from_msg(led_msg)
     
    def police_mode_leds(self):
        # Set LEDs based on battery level
        # Define colors for LEDs
        colors = {
            "red": ColorPeriod(color =ColorRGBA(r=1.0, g=0.0, b=0.0, a=1.0), frequency =8.0),
            "blue": ColorPeriod(color =ColorRGBA(r=0.0, g=0.0, b=1.0, a=1.0), frequency =8.0)
        }



        # Create and publish LEDControl message for each LED
        led_msg = LEDControl()
        
        led_msg.data = [ColorPeriod(color =ColorRGBA(r=0.0, g=0.0, b=0.0, a=0.0), frequency =0.0)]*40
        for i in range(38):
            led_msg.single_led_n = 0
            led_msg.control_type = 4 
            if i < 9:
                color = "blue"
                led_msg.data[i]=(colors[color])
            if i >=9 and i < 20:
                color = "blue"
                led_msg.data[i]=(colors[color])
            if i >= 20 and i < 29:
                color = "red"
                led_msg.data[i]=(colors[color])
            if i>= 29 and i < 39:
                color = "red"
                led_msg.data[i]=(colors[color])

        self.robot.led.set_leds_from_msg(led_msg)


    @staticmethod
    def get_velocity_to_target(target_detection: dai.ImgDetection, direction: str) -> Tuple[float, float]:
        multiplier = 1 if direction == FRONT_STREAM_NAME else -1
        detection_xcenter = (target_detection.xmax + target_detection.xmin) / 2
        detection_center_distance = 0.5 - detection_xcenter
        angular_velocity = detection_center_distance * \
            abs(detection_center_distance) * 50
        detection_width = target_detection.xmax - target_detection.xmin
        detection_width_difference = EXPECTED_TARGET_WIDTH - detection_width
        linear_velocity = multiplier * detection_width_difference * \
            abs(detection_width_difference) * 50
        return angular_velocity, linear_velocity


def other_direction(direction: str) -> Optional[str]:
    return OTHER_DIRECTIONS.get(direction)


def pick_detection(detections: List[dai.ImgDetection]) -> Detections:
    closest_detection = None
    closest_detection_size = -1
    other_detections = []
    for detection in detections:
        detection_size = detection.xmax - detection.xmin
        if detection.label in FOLLOWED_OBJECT_TYPES:
            if detection_size > closest_detection_size:
                other_detections.append(closest_detection)
                closest_detection = detection
                closest_detection_size = detection_size
            else:
                other_detections.append(detection)

    return Detections(other=[detection for detection in other_detections if detection], target=closest_detection)
