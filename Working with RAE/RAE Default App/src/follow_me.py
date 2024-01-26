from time import sleep
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Tuple
from datetime import datetime, timedelta

import robothub
import time
import depthai as dai
import os
import signal

from src.robot.robot import Robot
from src.robot.perception.camera import Camera
from src.robot.perception.detections import Detections, labelMap, create_detection_metadata
from src.robot.perception.pipeline import build_pipeline
from src.api.performance import measure_call_frequency
from src.utilities.logging import Log

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
        self.logger = Log()
        self.robot = Robot(self.logger)
        self.camera = Camera(self.logger)
        self.available_apps = []
        self.robot_status = None
        self.latest_detections = {
            FRONT_STREAM_NAME: Detections(), REAR_STREAM_NAME: Detections()}
        self.mode = AppMode.manual
        self.folow_me_direction = None
        self.last_detection_timestamp = datetime.now()

    def on_start(self):
        if not robothub.DEVICES:
            self.logger.error(
                "The default app requires an assigned device to run. "
                "Please go to RobotHub, navigate to the app's page, "
                "click the \"Reassign devices\" button and select a device."
            )
            self._stop(1)

        self.logger.info("Starting the app...")

        self.logger.info("Starting Robot")
        self.robot.start()
        sleep(2)
        self.logger.info("Starting robothub communicator...")
        self.init_robothub_communicator()
        sleep(2)
        self.logger.info("Starting streams...")
        self.init_streams()


    def on_stop(self):
        self.logger.info("Stopping the app...")
        self.robot.stop()
        self.camera.stop()

    def init_robothub_communicator(self):
        robothub.COMMUNICATOR.on_frontend(
            notification=self.on_fe_notification, request=self.on_fe_request)

    def init_streams(self):
        pipeline = build_pipeline(
            dai.CameraBoardSocket.CAM_B, FRONT_STREAM_NAME, dai.CameraBoardSocket.CAM_D, REAR_STREAM_NAME
        )
        self.camera.add_imu_ros_stream("imu")
        for stream_name in STREAM_NAMES:
            self.camera.add_rh_stream(stream_name)
            self.camera.add_ros_stream(stream_name)

        self.camera.start_pipeline(pipeline)
        for stream_name in STREAM_NAMES:
            self.camera.add_queue(f"{stream_name}", self.stream_callback_rh)
            self.camera.add_queue(
                f"{stream_name}_mjpeg", self.stream_callback_ros)
            self.camera.add_queue(f"{stream_name}_nn",
                                  self.control_callback_front)
        self.camera.add_queue("imu", self.stream_callback_imu)

    def stream_callback_rh(self, name: str, msg: dai.ImgFrame):
        detections = self.latest_detections[name]
        metadata = create_detection_metadata(
            detections, RESOLUTION_WIDTH, RESOLUTION_HEIGHT)
        color_frame = msg.getFrame()
        timestamp = int(time.time() * 1_000)
        self.camera.publish_rh(name, color_frame, timestamp, metadata)

    def stream_callback_ros(self, name: str, msg: dai.ImgFrame):
        self.camera.publish_ros(name, msg)
        
    def stream_callback_imu(self, name: str, msg: dai.IMUData):
        self.camera.publish_ros(name, msg)

    def on_fe_notification(self, session_id, unique_key, payload):
        if unique_key == "cmd_vel" and self.mode == AppMode.manual:
            self.robot.move(payload['linear'], payload['angular'])
        elif unique_key == "app_install":
            print("Received notification to app installation")
        elif unique_key == "rae_control_horn":
            self.robot.play_random_sfx()
        else:
            self.logger.info(f"Unique key: {unique_key}, payload: {payload}")

    def on_fe_request(self, session_id, unique_key, payload):
        if unique_key == "apps_get_list":
            return self.available_apps
        elif unique_key == "robot_status":
            print("Received notification to load robot status")
            if self.robot.get_battery() is None:
                return None
            return {
                "downloadSpeed": None,
                "diskTotal": None,
                "diskUsage": None,
                "batteryCapacity": self.robot.get_battery().capacity,
                "mappingPaused": False,
                "mappingRunning": False,
            }
        elif unique_key == "rae_control_leds":
            self.robot.set_leds(payload)
        elif unique_key == "rae_control_lcd":
            self.robot.display_face(payload)
        elif unique_key == "change_mode":
            self.last_detection_timestamp = datetime.now()
            self.folow_me_direction = None
            try:
                self.mode = AppMode[payload.get("mode")]
                self.logger.info(f'Robot mode set to "{self.mode.value}"')
            except KeyError:
                self.logger.error(
                    f"Unexpected mode \"{payload.get('mode')}\" was requested, ignoring")
        else:
            self.logger.info(f"Unique key: {unique_key}, payload: {payload}")

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

    def navigate_follow_me(self, detection_direction: str):
        current_detections = self.latest_detections[detection_direction]

        if not self.folow_me_direction and current_detections.target:
            self.logger.info(
                f'Spotted target in direction "{detection_direction}", following')
            self.folow_me_direction = detection_direction

        if self.folow_me_direction == detection_direction and not current_detections.target:
            other_detections = self.latest_detections[detection_direction]
            if other_detections.target:
                self.logger.info(
                    f'Lost target in direction "{self.folow_me_direction}", following in opposite direction')
                self.folow_me_direction = other_detections(detection_direction)
            else:
                self.logger.info(
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
            self.robot.move(linear_velocity, angular_velocity)

    def get_search_velocity(self) -> Tuple[float, float]:
        linear_velocity = 0
        angular_velocity = 0
        if datetime.now() > self.last_detection_timestamp + WAIT_BEFORE_STARTING_TO_ROTATE:
            linear_velocity = 0
            angular_velocity = 1.5
        return angular_velocity, linear_velocity

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
