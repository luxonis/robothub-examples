from http.server import BaseHTTPRequestHandler, HTTPServer
import multiprocessing as mp
import depthai as dai
import numpy as np
import importlib
import traceback
import threading
import logging
import time
import cv2

try:
    importlib.import_module('open3d')
except ImportError:
    import subprocess
    subprocess.check_call(['pip', 'install', 'open3d'])

import open3d as o3d

class PCRequestHandler(BaseHTTPRequestHandler):
  def log_message(self, format, *args):
    return
  
  def end_headers(self):
    self.send_header('Access-Control-Allow-Origin', '*')
    self.send_header('Access-Control-Allow-Methods', 'GET')
    self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    super().end_headers()
  def do_GET(self):
    data = self.server.data
    if self.path == '/pointcloud':
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

def work(intrinsics, resolution, camToWorld, stopEvent: mp.Event, colorQueue: mp.Queue, depthQueue: mp.Queue):
  server = PCHTTPServer(('', 38154), PCRequestHandler)
  server.data = bytes(0)
  server_thread = threading.Thread(target=server.serve_forever)
  server_thread.start()
  pinholeCameraIntrinsic = o3d.camera.PinholeCameraIntrinsic(
    resolution[0],
    resolution[1],
    intrinsics[0][0],
    intrinsics[1][1],
    intrinsics[0][2],
    intrinsics[1][2])

  lastFrame = time.time()

  while not stopEvent.is_set():
    try:
      if colorQueue.empty() or depthQueue.empty():
        stopEvent.wait(timeout=0.01)
        continue
      
      if time.time() - lastFrame < 1/20:
        continue
      lastFrame = time.time()

      colorImage, depthImage = colorQueue.get(), depthQueue.get()

      rgbd_image = o3d.geometry.RGBDImage.create_from_color_and_depth(
          o3d.geometry.Image(cv2.cvtColor(colorImage, cv2.COLOR_BGR2RGB)),
          o3d.geometry.Image(depthImage),
          convert_rgb_to_intensity=False,
          depth_trunc=20000,
          depth_scale=1000.0
      )

      pcd = o3d.geometry.PointCloud.create_from_rgbd_image(rgbd_image, pinholeCameraIntrinsic)

      # downsample
      pcd = pcd.voxel_down_sample(voxel_size=0.015)

      # remove_noise
      pcd = pcd.remove_statistical_outlier(30, 0.1)[0]

      # Rotate to sit along the -Z Axis
      pcd.rotate(camToWorld, center=np.array([0,0,0],dtype=np.float64))

      server.data = np.concatenate((np.asarray(pcd.points, dtype=np.float64).astype(np.float32), np.asarray(pcd.colors, dtype=np.float64).astype(np.float32))).tobytes()
      
    except KeyboardInterrupt:
      stopEvent.set()
    except BaseException as e:
      logging.error(f"Exception occured in worker thread, {e}")
      traceback.print_exc()
  logging.info("Worker finished")
  server.shutdown()
  server_thread.join()

class Worker:
  def __init__(self, intrinsics, resolution, camToWorld):
    self._colorQueue = mp.Queue()
    self._depthQueue = mp.Queue()
    self._stopEvent = mp.Event()
    self._process = mp.Process(target=work, args=(intrinsics, resolution, camToWorld, self._stopEvent, self._colorQueue, self._depthQueue,))
    self._process.start()

  def __del__(self):
    self._stopEvent.set()
    if self._process.is_alive():
      self._process.join()
      self._process.close()

  def add(self, colorImage, depthImage):
    if self._colorQueue.empty() and self._depthQueue.empty():
      self._colorQueue.put(colorImage)
      self._depthQueue.put(depthImage)

class Pointcloud:
  def __init__(self, fps=15):
    self._fps = fps
    self._res = (0,0)
    self._calibData = None
    self._intrinsics = None
    self._pinholeCameraIntrinsic = None
    self._camToWorld = np.array([
      [-2, 0, 0],
      [ 0,-2, 0],
      [ 0, 0, 2]]).astype(np.float64)
    
    self._frame = 0
    self._workers: list[Worker] = []

    self._colorFrame = []
    self._depthFrame = []

  def __del__(self):
    for worker in self._workers:
      worker._stopEvent.set()

  def _create_pc(self):
    if len(self._colorFrame) == 0 or len(self._depthFrame) == 0:
      return
    
    self._workers[0].add(self._colorFrame, self._depthFrame)
    self._colorFrame = []
    self._depthFrame = []
  
  def configure_camera(self, camera: dai.node.ColorCamera):
    self._res = camera.getVideoSize()

  def configure_device(self, device: dai.Device):
    self._calibData = device.readCalibration()
    self._intrinsics = self._calibData.getCameraIntrinsics(dai.CameraBoardSocket.RGB, dai.Size2f(self._res[0], self._res[1]))
    self._workers.append(Worker(self._intrinsics, self._res, self._camToWorld))

  def add_color(self, colorFrame: np.ndarray):
    self._colorFrame = colorFrame
    self._create_pc()

  def add_depth(self, depthFrame: np.ndarray):
    self._depthFrame = depthFrame
    self._create_pc()