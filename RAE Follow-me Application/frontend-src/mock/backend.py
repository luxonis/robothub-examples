import asyncio
import logging as log
import threading
import rclpy
import time
import math
import json
import random
import subprocess
import os
import signal
import sqlite3
import uuid
import tf2_ros

from PIL import Image

from pathlib import Path
from websockets.server import serve
from typing import Any, Callable, Dict, Type
from rclpy.executors import Executor, MultiThreadedExecutor
from rclpy.publisher import Publisher
from rclpy.subscription import Subscription
from geometry_msgs.msg import Twist
from std_msgs.msg import String
from nav_msgs.msg import OccupancyGrid

QOS_PROFILE = 10
ROS2_NAMESPACE = '/rae'

DATABASE = os.path.join(os.getcwd(), "database.sqlite")

ROBOTHUB_APPS = [
    {
        "globalIdentifier": '1',
        "name": 'Follow me',
        "description": 'Ask rae to follow you or someone else.',
    },
    {
        "globalIdentifier": '2',
        "name": 'Hide and seek',
        "description": 'Play hide and seek with rae',
    },
    {
        "globalIdentifier": '3',
        "name": 'Sentry',
        "description": 'Activate sentry mode.',
    },
    {
        "globalIdentifier": '4',
        "name": 'Find Item',
        "description": 'Lost your keys? Ask rae to find them',
    }
]

INSTALLED_APPS = []


class MessageFactory:
    def __init__(self):
        self._msg_types = {
            "Twist": Twist,
            "String": String,
            "OccupancyGrid": OccupancyGrid,
        }

    def get_msg_type(self, msg_type_str: str):
        return self._msg_types.get(msg_type_str)

    def create_msg(self, msg_type: str, payload: dict) -> Any:
        if msg_type == "Twist":
            return self._create_twist_msg(payload)
        if msg_type == "String":
            return self._create_string_msg(payload)
        else:
            raise ValueError(f"Unknown message type '{msg_type}'")

    def _create_twist_msg(self, payload: dict) -> Twist:
        twist_msg = Twist()
        twist_msg.linear.x = float(payload['linear'])
        twist_msg.linear.y = 0.0
        twist_msg.linear.z = 0.0
        twist_msg.angular.x = 0.0
        twist_msg.angular.y = 0.0
        twist_msg.angular.z = float(payload['angular'])

        return twist_msg

    def _create_string_msg(self, payload: dict) -> String:
        string_msg = String()
        string_msg.data = payload['message']

        return string_msg


class ROS2Manager:
    def __init__(self, name: str) -> None:
        self._name = name
        self._context: rclpy.context.Context | None = None
        self._node: rclpy.node.Node | None = None
        self._publishers: dict[str, Publisher] = {}
        self._subscribers: dict[str, Subscription] = {}
        self._message_factory = MessageFactory()

    def get_node(self):
        return self._node

    def start(self) -> None:
        self._context = rclpy.Context()
        self._context.init()
        print("ROS2 context initialized.") # info

        self._node = rclpy.create_node(self._name, context=self._context, namespace=ROS2_NAMESPACE)
        print(f"Created ROS2 node with name: {self._name}...") # info
        self._executor = MultiThreadedExecutor(num_threads=2, context=self._context)
        self._executor.add_node(self._node)
        self._executor_thread = threading.Thread(target=self._executor.spin)
        self._executor_thread.start()
        print(f"Node started!") # info

    def stop(self) -> None:
        if not self._context:
            print("ROS2 context is already stopped") # info
            return

        if self._executor_thread:
            self._executor.shutdown()
            self._executor_thread.join()
            self._executor_thread = None

        if self._node:
            print("Destroying ROS2 node...") # info
            self._node.destroy_node()
            self._node = None

        if self._context:
            print("Shutting down ROS2 context...") # info
            self._context.try_shutdown()
            self._context.destroy()
            self._context = None

    def _destroy_publishers_and_subscribers(self):
        for topic_name, publisher in self._publishers.items():
            print(f"Destroying {topic_name} publisher...") # info
            self._node.destroy_publisher(publisher)

        for topic_name, subscriber in self._subscribers.items():
            print(f"Destroying {topic_name} subscriber...") # info
            self._node.destroy_subscription(subscriber)

        self._publishers.clear()
        self._subscribers.clear()

    def create_publisher(self, topic_name: str, msg_type_str: str, qos_profile: int = QOS_PROFILE) -> None:
        if topic_name not in self._publishers:
            msg_type = self._message_factory.get_msg_type(msg_type_str)
            if msg_type is not None:
                print(f"Creating {topic_name} publisher") # info
                self._publishers[topic_name] = self._node.create_publisher(msg_type, topic_name, qos_profile)
            else:
                print(f"Unknown message type '{msg_type_str}'") # warning

    def publish(self, topic_name: str, payload: dict) -> None:
        if topic_name in self._publishers:
            publisher = self._publishers[topic_name]
            msg_type_str = publisher.msg_type.__name__
            msg = self._message_factory.create_msg(msg_type_str, payload)
            self._node.get_logger().info(f"Publishing message to topic '{topic_name}': {msg}")
            publisher.publish(msg)
        else:
            print(f"No publisher found for topic '{topic_name}'") # warning

    def create_subscriber(self, topic_name: str, msg_type_str: str, callback=None, qos_profile: int = QOS_PROFILE) -> None:
        if topic_name not in self._subscribers:
            msg_type = self._message_factory.get_msg_type(msg_type_str)
            if msg_type is not None:
                if callback is None:
                    callback = self._default_callback

                print(f"Creating {topic_name} subscriber") # info
                self._subscribers[topic_name] = self._node.create_subscription(msg_type, topic_name, callback, qos_profile)
            else:
                print(f"Unknown message type '{msg_type_str}'") # warning

    def _default_callback(self, msg) -> None:
        print(f"[Default callback] Received message: {msg}") # info


class Mapping:
    def __init__(self):
        self.mapping_running = False
        self.mapping_paused = False
        self.proc = None
        self.db = None

        try:
            c = self.get_db().cursor()
            c.execute("CREATE TABLE IF NOT EXISTS maps (id integer PRIMARY KEY, id_ext text NOT NULL, name text NOT NULL)")
            c.close()
        except Exception as e:
            print(e)

    def get_db(self):
        if self.db is None:
            self.db = sqlite3.connect(DATABASE)
        return self.db

    def start_mapping(self):
        self.mapping_running = True

        env = dict(os.environ)

        self.proc = subprocess.Popen(
            "bash ros_start.sh",
            shell=True,
            env=env,
            preexec_fn=os.setsid
        )

    def stop_mapping(self):
        self.mapping_running = False

        if self.proc is not None:
            pgid = os.getpgid(self.proc.pid)
            os.killpg(pgid, signal.SIGTERM)

    def pause_mapping(self):
        self.mapping_paused = True
        self.stop_mapping()

    def resume_mapping(self):
        self.mapping_paused = False
        self.start_mapping()

    def finish_mapping(self, name):
        source_path = Path(__file__).resolve()
        source_dir = source_path.parent

        map_id = random.randint(0, 100)
        subprocess.run(["bash", "ros_map_save.sh", "map_" + str(map_id)])

        filename_pgm = str(source_dir) + "/maps/map_" + str(map_id) + ".pgm"
        filename_png = str(source_dir) + "/maps/map_" + str(map_id) + ".png"

        with Image.open(filename_pgm) as im:
            im.save(filename_png)

        with self.get_db():
            try:
                c = self.get_db().cursor()
                c.execute("insert into maps (id_ext, name) values (?, ?)", (map_id, name))
                c.close()
            except Exception as e:
                print(e)

        self.stop_mapping()

    def get_maps(self):
        data = []

        with self.get_db():
            try:
                c = self.get_db().cursor()
                c.execute("SELECT id_ext, name FROM maps")
                maps = c.fetchall()
                c.close()

                for map in maps:
                    data.append({
                        "mapFile": "/mock/maps/map_" + str(map[0]) + ".png",
                        "mapId": map[0],
                        "name": map[1],
                        "description": '',
                    })
            except Exception as e:
                print(e)

        return data

    def delete_map(self, id):
        with self.get_db():
            try:
                c = self.get_db().cursor()
                c.execute("DELETE FROM maps WHERE id_ext=?", (id,))
                c.close()
            except Exception as e:
                print(e)


class WebsocketServer:
    def __init__(self, ros2):
        self.clients = set()
        self.mapping = Mapping()

        self.ros2 = ros2
        self.ros2.create_publisher('/cmd_vel', 'Twist')
        self.ros2.create_subscriber('/map', 'OccupancyGrid', self.broadcast_map)

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self.ros2.get_node())
        self.timer = self.ros2.get_node().create_timer(0.1, self.lookup_transform)

    def lookup_transform(self):
        if not self.mapping.mapping_running:
            return

        try:
            transform = self.tf_buffer.lookup_transform('map', 'base_footprint', rclpy.time.Time())

            asyncio.run(self.broadcast(json.dumps({
                "type": "notification",
                "key": "mapping_robot_position",
                "payload": {
                    "translation": {
                        "x": transform.transform.translation.x,
                        "y": transform.transform.translation.y,
                        "z": transform.transform.translation.z,
                    },
                    "rotation": {
                        "x": transform.transform.rotation.x,
                        "y": transform.transform.rotation.y,
                        "z": transform.transform.rotation.z,
                        "w": transform.transform.rotation.w,
                    },
                },
            })))
        except tf2_ros.LookupException as e:
            print("Transform lookup failed:", e)
        except tf2_ros.ExtrapolationException as e:
            print("Transform extrapolation failed:", e)
        except Exception as e:
            print("LookUp Transform failed:", e)

    async def broadcast(self, message):
        for websocket in self.clients.copy():
            try:
                await websocket.send(message)
            except websockets.ConnectionClosed:
                pass

    def broadcast_map(self, data):
        payload = {}
        payload["header"] = {
            "frame_id": data.header.frame_id,
            "stamp": {
                "sec": data.header.stamp.sec,
                "nanosec": data.header.stamp.nanosec,
            },
        }
        payload["info"] = {
            "map_load_time": {
                "sec": data.info.map_load_time.sec,
                "nanosec": data.info.map_load_time.nanosec,
            },
            "resolution": data.info.resolution,
            "width": data.info.width,
            "height": data.info.height,
            "origin": {
                "position": {
                    "x": data.info.origin.position.x,
                    "y": data.info.origin.position.y,
                    "z": data.info.origin.position.z,
                },
                "orientation": {
                    "x": data.info.origin.orientation.x,
                    "y": data.info.origin.orientation.y,
                    "z": data.info.origin.orientation.z,
                    "w": data.info.origin.orientation.w,
                },
            }
        }
        payload["data"] = list(data.data)

        asyncio.run(self.broadcast(json.dumps({
            "type": "notification",
            "key": "mapping_map",
            "payload": {
                "mapData": payload,
            },
        })))

    async def handler(self, websocket):
        self.clients.add(websocket)

        try:
            async for message in websocket:
                if message is not None:
                    print(message)

                    try:
                        data = json.loads(message)

                        try:
                            if data["type"] == "notification":
                                if data["key"] == "cmd_vel":
                                    self.ros2.publish('/cmd_vel', { 'linear': data["payload"]["linear"] * 0.1, 'angular': data["payload"]["angular"] * 0.1 })
                                elif data["key"] == "app_install":
                                    item = [i for i in ROBOTHUB_APPS if i["globalIdentifier"] == data["payload"]["app_identifier"]][0]
                                    if item is not None:
                                        INSTALLED_APPS.append({
                                            "appId": str(uuid.uuid4()),
                                            "appIdentifier": item["globalIdentifier"],
                                            "appSourceUpToDate": True,
                                            "configUpToDate": True,
                                            "expectedStatus": 'running',
                                            "hasEditor": False,
                                            "hasFrontend": False,
                                            "name": item["name"],
                                            "robotAppId": str(uuid.uuid4()),
                                            "status": 'running',
                                            "studioRunning": True,
                                        })
                            elif data["type"] == "request":
                                if data["key"] == "apps_get_list":
                                    await websocket.send(json.dumps({
                                        "type": "response",
                                        "key": data["key"],
                                        "requestId": data["requestId"],
                                        "payload": ROBOTHUB_APPS,
                                    }))
                                elif data["key"] == "rcv_status":
                                    await websocket.send(json.dumps({
                                        "type": "response",
                                        "key": data["key"],
                                        "requestId": data["requestId"],
                                        "payload": INSTALLED_APPS,
                                    }))
                                elif data["key"] == "robot_status":
                                    await websocket.send(json.dumps({
                                        "type": "response",
                                        "key": data["key"],
                                        "requestId": data["requestId"],
                                        "payload": {
                                            "downloadSpeed": random.randint(0, 100),
                                            "diskTotal": random.randint(50, 100),
                                            "diskUsage": random.randint(0, 50),
                                            "batteryCapacity": random.randint(0, 100),
                                            "mappingRunning": self.mapping.mapping_running,
                                            "mappingPaused": self.mapping.mapping_paused,
                                        },
                                    }))
                                elif data["key"] == "mapping_start":
                                    self.mapping.start_mapping()
                                    await websocket.send(json.dumps({
                                        "type": "response",
                                        "key": data["key"],
                                        "requestId": data["requestId"],
                                        "payload": {},
                                    }))
                                elif data["key"] == "mapping_stop":
                                    self.mapping.stop_mapping()
                                    await websocket.send(json.dumps({
                                        "type": "response",
                                        "key": data["key"],
                                        "requestId": data["requestId"],
                                        "payload": {},
                                    }))
                                elif data["key"] == "mapping_pause":
                                    self.mapping.pause_mapping()
                                    await websocket.send(json.dumps({
                                        "type": "response",
                                        "key": data["key"],
                                        "requestId": data["requestId"],
                                        "payload": {},
                                    }))
                                elif data["key"] == "mapping_restore":
                                    self.mapping.resume_mapping()
                                    await websocket.send(json.dumps({
                                        "type": "response",
                                        "key": data["key"],
                                        "requestId": data["requestId"],
                                        "payload": {},
                                    }))
                                elif data["key"] == "mapping_finish":
                                    self.mapping.finish_mapping(data["payload"]["name"])
                                    await websocket.send(json.dumps({
                                        "type": "response",
                                        "key": data["key"],
                                        "requestId": data["requestId"],
                                        "payload": {},
                                    }))
                                elif data["key"] == "mapping_maps":
                                    await websocket.send(json.dumps({
                                        "type": "response",
                                        "key": data["key"],
                                        "requestId": data["requestId"],
                                        "payload": self.mapping.get_maps(),
                                    }))
                                elif data["key"] == "mapping_map_delete":
                                    self.mapping.delete_map(data["payload"]["mapId"])
                                    await websocket.send(json.dumps({
                                        "type": "response",
                                        "key": data["key"],
                                        "requestId": data["requestId"],
                                        "payload": {},
                                    }))
                        except Exception as e:
                            print("Error occured!", e)
                    except:
                        print("Cannot parse message!")
        finally:
            self.clients.remove(websocket)


async def main():
    ros2 = ROS2Manager('base_container')
    ros2.start()

    wsServer = WebsocketServer(ros2)
    async with serve(wsServer.handler, "localhost", 8765):
        await asyncio.Future()  # run forever

asyncio.run(main())
