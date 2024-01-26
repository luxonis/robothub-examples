from http.server import BaseHTTPRequestHandler, HTTPServer
from robothub_oak.components.stereo import Stereo
from robothub_oak.components.camera import Camera
from robothub_oak.commands import Command
from robothub_oak.device import Device
from pointcloud import Pointcloud
import threading
import json
from imu import Context, calculate_IMU_offset_step, process_packets

class IMURequestHandler(BaseHTTPRequestHandler):
  def log_message(self, format, *args):
    return
  
  def end_headers(self):
    self.send_header('Access-Control-Allow-Origin', '*')
    self.send_header('Access-Control-Allow-Methods', 'GET')
    self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    super().end_headers()
  def do_GET(self):
    data = json.dumps(self.server.data).encode('utf-8')
    if self.path == '/imu':
      self.send_response(200)
      self.send_header('Content-type','application/octet-stream')
      self.end_headers()
      self.wfile.write(data)
    else:
      self.send_response(404)

class PCHTTPServer(HTTPServer):
  def __init__(self, *args, data=None, **kwargs):
    self.data = data
    super().__init__(*args, **kwargs)

  def shutdown(self):
    self.socket.close()
    HTTPServer.shutdown(self)


class CreatePointcloudCommand(Command):
    def __init__(self, device: 'Device', color: Camera, stereo: Stereo, pointcloud: Pointcloud) -> None:
        super().__init__(device=device)
        self._pointcloud = pointcloud
        self._color = color
        self._stereo = stereo

    def execute(self):
        server = PCHTTPServer(('', 38155), IMURequestHandler)
        server.data = {
            "pitch": 0,
            "yaw": 0,
            "roll": 0
        }
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.start()
  
        oak = self.hub_camera.oak_camera
        imu = oak.create_imu()
        imu.config_imu(report_rate=10, batch_report_threshold=2)
        print(oak.device.getConnectedIMU())

        # Set the init values
        Iter = 0

        ctx = Context()

        def callback(imuData):
            nonlocal Iter, ctx, server
            Iter += 1
            if Iter < ctx.Samples:
                calculate_IMU_offset_step(imuData.data, ctx)
                print(ctx.GyroErrorX, ctx.GyroErrorY, ctx.GyroErrorZ)
            elif Iter == ctx.Samples:
                ctx.finish_IMU_offset()
            else:
                server.data["pitch"], server.data["yaw"], server.data["roll"] = process_packets(imuData.data, ctx)
                # with open("/public/test.txt", 'w') as file:
                #     pitch, yaw, roll = process_packets(imuData.data, ctx)
                #     file.write(f'{{"pitch": {pitch}, "yaw": {yaw}, "roll": {roll}}}')
            

        self.hub_camera.callback(imu, callback=callback)
        self._pointcloud.configure_camera(self._color.camera_component.node)
        self._pointcloud.configure_device(self.hub_camera.device)

        self.hub_camera.callback(self._color.camera_component.out.camera,  lambda packet: self._pointcloud.add_color(packet.frame))
        self.hub_camera.callback(self._stereo.stereo_component.out.depth, lambda packet: self._pointcloud.add_depth(packet.frame))

    def get_component(self) -> Pointcloud:
        return self._pointcloud

def get_pointcloud(self, color: Camera, stereo: Stereo) -> Pointcloud:
    pointcloud = Pointcloud()
    self._command_history.push(CreatePointcloudCommand(self, color, stereo, pointcloud))
    return pointcloud

setattr(Device, "get_pointcloud", get_pointcloud)