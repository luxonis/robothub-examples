import time
import logging as log
import depthai as dai

class ExampleApplication(robothub.RobotHubApplication):
    def on_start(self):
        fps = robothub.CONFIGURATION['stream_fps']
        log.info(f'Stream FPS set to {fps}, connecting to devices...')

        # connect to the device(s), build pipeline and upload it to the device
        self.connect(fps)

        # create polling thread and start it
        run_polling_thread = robothub.threading.Thread(target = self.polling_thread, name="PollingThread", daemon=False)
        run_polling_thread.start()


    def connect(self, fps):
        # connect to every assigned device, open a color stream

        self.devices = dict()
        self.streams = dict()
        self.outQueues = dict()

        for device in robothub.DEVICES:
            mxid = device.oak["serialNumber"]
            name = device.oak['productName']

            start_time = time.time()
            give_up_time = start_time + 10
            cameras = None
            while time.time() < give_up_time and self.running:
                try:
                    self.devices[mxid] = dai.Device(mxid)
                    cameras = self.devices[mxid].getConnectedCameras()
                    log.info(f'Connected device "{name}" with sensors: {cameras}')
                    break
                except RuntimeError as e:
                    # If device can't be connected to on first try, wait 0.1 seconds and try again. 
                    log.info(f"Error while trying to connect {name}: {e}")
                    self.wait(0.1)
                    continue
            # check if the device has RGB sensor
            color = False
            if cameras:
                for _camera in cameras:
                    if _camera.name.upper() == 'RGB':
                        color = True
                if color:
                    # if it does build a pipeline and start it
                    pipeline = self.build_pipeline(mxid, fps)
                    self.devices[mxid].startPipeline(pipeline)
                    self.streams[mxid] = robothub.STREAMS.create_video(mxid, f'stream_{mxid}', f'{name} Color Stream')
                    self.outQueues[mxid] = self.devices[mxid].getOutputQueue(name=mxid, maxSize=2, blocking=True)
                    log.info(f'Device "{name}": Started 1080p@{fps}FPS Color Stream')
                else:
                    # if it does not, skip
                    log.info(f'Could not start color stream for device {name} as it does not have a color sensor')
            else:
                # if cameras is None, device connection or collecting camera info failed
                log.info(f'Device "{name}" could not be connected within 10s timeout')

    def polling_thread(self):
        # Create polling thread
        while self.running:
            self.process_output()
            self.wait(0.001)

    def build_pipeline(self, mxid, fps):
        # Create pipeline
        pipeline = dai.Pipeline()

        # Define sources and outputs
        camRgb = pipeline.create(dai.node.ColorCamera)
        ve = pipeline.create(dai.node.VideoEncoder)
        veOut = pipeline.create(dai.node.XLinkOut)
        veOut.setStreamName(mxid)

        # Properties
        camRgb.setBoardSocket(dai.CameraBoardSocket.RGB)
        camRgb.setFps(fps)
        camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)

        # Create encoder, consuming the frames and encoding them using H.264 / H.265 encoding
        ve.setDefaultProfilePreset(fps, dai.VideoEncoderProperties.Profile.H264_MAIN)

        # Linking
        camRgb.video.link(ve.input)
        ve.bitstream.link(veOut.input)

        return pipeline

    def process_output(self):
        # Output queues will be used to get the encoded data from the outputs defined above
        for id in self.outQueues:
            # Try to get the frame bytes data from the queue for the stream. If no frame is in output queue, pass
            frame = self.outQueues[id].tryGet()
            if frame:
                frame_bytes = bytes(frame.getData())
                # create timestamp for the video stream
                timestamp = int(time.time() * 1_000)
                self.streams[id].publish_video_data(frame_bytes, timestamp, None)


    def on_stop(self):
        log.info('Stopping App')

        try:
            self.run_polling_thread.join()
        except:
            log.debug('Polling thread join excepted with {e}')
        try: 
            robothub.STREAMS.destroy_all_streams()
        except BaseException as e:
            log.debug(f'Destroy all streams excepted with: {e}')
        for device in self.devices.values():
            try:
                device.close()
            except BaseException as e:
                log.debug(f'Device close failed with error: {e}')

