import time
import logging as log
import os
import contextlib
from depthai_sdk import OakCamera, FramePacket

class ExampleApplication(robothub.RobotHubApplication):
    def on_start(self):
        # This is the entrypoint of your App. 
        # It should be used:
        #   - As a constructor for your App
        #   - To connect/initialize devices, download blobs if needed, initialize streams
        # on_start() must terminate
        # If on_start() excepts, agent will endlessly restart the app
        # If on_start() returns, start_execution() is called

        # In this App, we will log Machine ID and Name of the first available device (from robothub.DEVICES, which contains all devices assigned to the app)
        assigned_id = robothub.DEVICES[0].oak.get('serialNumber')
        log.info(f'Assigned device: {assigned_id}')

        # Then we will log loaded configuration
        log.info(f'Configuration: {robothub.CONFIGURATION}')

        # Then we will connect to the device with DepthAI
        self.dai_device = DaiDevice(self, assigned_id)
        # Use a method to get device name and connected sensors
        self.dai_device.get_device_info()
        log.info(f'Device {self.dai_device.device_name} connected, detected sensors: {str(self.dai_device.cameras)}')

        # And initialize the person detection stream
        self.dai_device.initialize_person_detection_stream()
        log.info('Starting person detection stream...')

        # Initialize a thread to poll the device -> As in depthai_sdk, polling the device automatically calls callbacks
        self.run_polling_thread = robothub.threading.Thread(target = self.polling_thread, name="PollingThread", daemon=False)

        # And finnaly add a callback. App will constantly call it as long as it is running. If multiple callbacks are added, they will be called sequentially in a single thread. 
        robothub.add_loop_callback(self.report)
        
        # Start the device and run the polling thread
        self.dai_device.start()
        self.run_polling_thread.start()

    def report(self):
        # This is callback which will report device info & stats to the cloud. It needs to include a self.wait() for performance reasons.
        device_info = self.dai_device._device_info_report()
        device_stats = self.dai_device._device_stats_report()
        robothub.AGENT.publish_device_info(device_info)
        robothub.AGENT.publish_device_stats(device_stats)
        self.wait(2)
    
    def polling_thread(self):
        # Periodically polls the device, indirectly calling self.dai_device.detection_cb() defined on line 272 which sends packets to Agent through a StreamHandle.publish_video_data() method from the RobotHub SDK
        log.debug('Starting device polling loop')
        while not self.stop_event.is_set():
            self.dai_device.oak.poll()
            self.wait(0.01) # With this sleep we will poll at most 100 times a second, which is plenty, since our pipeline definitely won't be faster

    def on_stop(self):
        # Needs to be correctly implemented to gracefully shutdown the App (when a stop is requested/when the app crashes) 
        # on_stop() should, in general, be implemented to: 
        #   - destroy streams 
        #   - disconnect devices 
        #   - join threads if any have been started
        #   - reliably reset the app's state - depends on specifics of the app
        #
        # In this case, on_stop() will join the polling thread, the device report thread, close streams and then disconnect devices. 
        # A couple important details:
        #   - each join is wrapped in a try & except block. If the app stops before the joined thread is initialized, an Exception is raised. Exceptions in on_stop() will most likely cause the App to deadlock so we wrap it in a try & except block to prevent this.  
        #   - device exit is done as the last step to prevent e.g. a stream asking for frames from a device that has already been exited - again this would raise an Exception and deadlock.
        try:
            self.run_polling_thread.join()
        except:
            log.debug('Polling thread join excepted with {e}')
        try: 
            robothub.STREAMS.destroy_all_streams()
        except BaseException as e:
            raise Exception(f'Destroy all streams excepted with: {e}')
        try:
            if self.dai_device.state != robothub.DeviceState.DISCONNECTED:
                with open(os.devnull, 'w') as devnull:
                    with contextlib.redirect_stdout(devnull):
                        self.dai_device.oak.__exit__(Exception, 'Device disconnected - app shutting down', None)
        except BaseException as e:
            raise Exception(f'Could not exit device error: {e}')



class DaiDevice(robothub.RobotHubDevice):
    def __init__(self, app, mx_id):
        self.app = app
        self.id = mx_id
        self.state = robothub.DeviceState.UNKNOWN
        self.cameras = {}
        self.oak = OakCamera(self.id)
        self.eeprom_data = None
        self.device_name = "UNKNOWN"

    def start(self, reattempt_time = 1) -> None:
        # Uses the depthai_sdk to load a pipeline to a connected device
        log.debug('starting')
        while not self.app.stop_event.is_set():
            try:
                with open(os.devnull, 'w') as devnull:
                    with contextlib.redirect_stdout(devnull):
                        self.oak.start(blocking = False)
                self.state = robothub.DeviceState.CONNECTED
                log.debug('Succesfully started device')
                return
            except BaseException as err:
                log.warning(f"Cannot start device {self.id}: {err}")
            time.sleep(reattempt_time)
        log.debug('EXITED without starting')

    def _device_info_report(self) -> dict:
        """Returns device info"""
        # Function designed to gather device information which is then sent to the cloud.
        info = {
            'mxid': self.id,
            'state': self.state.value,
            'protocol': 'unknown',
            'platform': 'unknown',
            'product_name': 'unknown',
            'board_name': 'unknown',
            'board_rev': 'unknown',
            'bootloader_version': 'unknown',
        }
        try:
            info['bootloader_version'] = self.oak._oak.device.getBootloaderVersion()
        except:
            pass
        try:
            device_info = self.oak._oak.device.getDeviceInfo()
        except:
            device_info = None
        try:
            eeprom_data = self.oak._oak.device.readFactoryCalibration().getEepromData()
        except:
            try:
                eeprom_data = self.oak._oak.device.readCalibration().getEepromData()
            except:
                try: 
                    eeprom_data = self.oak._oak.device.readCalibration2().getEepromData()
                except:
                    eeprom_data = None  # Could be due to some malfunction with the device, or simply device is disconnected currently.
        if eeprom_data:
                info['product_name'] = eeprom_data.productName
                info['board_name'] = eeprom_data.boardName
                info['board_rev'] = eeprom_data.boardRev
        if device_info:
            info['protocol'] = device_info.protocol.name
            info['platform'] = device_info.platform.name
        return info

    def _device_stats_report(self) -> dict:
        """Returns device stats"""
        # Function designed to gather device stats which are then sent to the cloud.
        stats = {
            'mxid': self.id,
            'css_usage': 0,
            'mss_usage': 0,
            'ddr_mem_free': 0,
            'ddr_mem_total': 1,
            'cmx_mem_free': 0,
            'cmx_mem_total': 1,
            'css_temp': 0,
            'mss_temp': 0,
            'upa_temp': 0,
            'dss_temp': 0,
            'temp': 0,
        }
        try:
            css_cpu_usage = self.oak._oak.device.getLeonCssCpuUsage().average
            mss_cpu_usage = self.oak._oak.device.getLeonMssCpuUsage().average
            cmx_mem_usage = self.oak._oak.device.getCmxMemoryUsage()
            ddr_mem_usage = self.oak._oak.device.getDdrMemoryUsage()
            chip_temp = self.oak._oak.device.getChipTemperature()
        except:
            css_cpu_usage = None
            mss_cpu_usage = None
            cmx_mem_usage = None
            ddr_mem_usage = None
            chip_temp = None
        if css_cpu_usage:
            stats['css_usage'] = int(100*css_cpu_usage)
            stats['mss_usage'] = int(100*mss_cpu_usage)
            stats['ddr_mem_free'] = int(ddr_mem_usage.total - ddr_mem_usage.used)
            stats['ddr_mem_total'] = int(ddr_mem_usage.total)
            stats['cmx_mem_free'] = int(cmx_mem_usage.total - cmx_mem_usage.used)
            stats['cmx_mem_total'] = int(cmx_mem_usage.total)
            stats['css_temp'] = int(100*chip_temp.css)
            stats['mss_temp'] = int(100*chip_temp.mss)
            stats['upa_temp'] = int(100*chip_temp.upa)
            stats['dss_temp'] = int(100*chip_temp.dss)
            stats['temp'] = int(100*chip_temp.average)
        return stats

    def get_device_info(self) -> None:
        """Saves camera sensors and device name"""
        log.debug('connecting device')
        self.cameras = self.oak._oak.device.getCameraSensorNames()
        try:
            self.eeprom_data = self.oak._oak.device.readFactoryCalibration().getEepromData()
        except:
            try:
                self.eeprom_data = self.oak._oak.device.readCalibration().getEepromData()
            except:
                try: 
                    self.eeprom_data = self.oak._oak.device.readCalibration2().getEepromData()
                except:
                    self.eeprom_data = None  # Could be due to some malfunction with the device, or simply device is disconnected currently.
        try:
            self.device_name = self.oak._oak.device.getDeviceName()
        except:
            pass

    def initialize_person_detection_stream(self, resolution = '400p', fps = 30, stream_id = 'person_detection', name = 'Person Detection') -> None:
        # Function designed to initialize a pipeline which will stream H264 encoded RGB video with visualized person detections

        # 1. Some safety checks
        if len(self.cameras.keys()) == 0:
            raise Exception('Cannot initialize stream with no sensors')
        color = False
        for camera_ in self.cameras.keys():
            if camera_.name.upper() == 'RGB':
                color = True
        if color == False:
            raise Exception('Cannot initialize person detection stream, no sensor supports RGB')

        log.debug('sending stream wish')
        # 2. use the robothub.STREAMS.create_video function to have the Agent create a stream. 
        #   - First argument needs to be Machine ID of device that is going to stream
        #   - Second stream is unique ID of the stream
        #   - Third argument is the name of the stream in Live View in the cloud
        person_detection_stream_handle = robothub.STREAMS.create_video(self.id, stream_id, name + f' {resolution}@{fps}FPS')

        # 3. create a pipeline through depthai_sdk 
        camera = self.oak.create_camera('color', resolution = resolution, fps=fps, encode='h264')
        # 4. get parameters of the color sensor
        width = camera.node.getResolutionWidth()
        height = camera.node.getResolutionHeight()

        # 5. Add a neural network for person detection to the same pipeline and configure it
        det = self.oak.create_nn('person-detection-retail-0013', camera, nn_type='mobilenet')
        det.config_nn(conf_threshold=0.1)
        # 6. Define a callback for outputs of the pipeline
        def detection_cb(packet):
            # 7. Our pipeline will have multiple outputs
            packet_1 = packet['1_bitstream']
            packet_2 = packet['2_out;0_video']
            detections_metadata = []
            for detection in packet_2.detections:
                # 8. If packet_2 contains any detections, format them to a dictionary and add it to metadata
                bbox = [detection.top_left[0], detection.top_left[1], detection.bottom_right[0], detection.bottom_right[1]]
                detections_metadata.append({
                    'bbox': bbox,
                    'label': 'Person',
                    'color': [216, 92, 93]
                })
            metadata = {
                'platform': 'robothub',
                'frame_shape': [height, width, 3],
                'config': {
                    'img_scale': 1.0,
                    'show_fps': True,
                    'detection': {
                        'thickness': 1,
                        'fill_transparency': 0.15,
                        'box_roundness': 0,
                        'color': [255, 255, 255],
                        'bbox_style': 0,
                        'line_width': 0.5,
                        'line_height': 0.5,
                        'hide_label': False,
                        'label_position': 0,
                        'label_padding': 10,
                    },
                    'text': {
                        'font_color': [255, 255, 0],
                        'font_transparency': 0.5,
                        'font_scale': 1.0,
                        'font_thickness': 2,
                        'font_position': 0,
                        'bg_transparency': 0.5,
                        'bg_color': [0, 0, 0],
                    },
                },
                'objects': [
                    {
                        'type': 'detections',
                        'detections': detections_metadata
                    }
                ]
            }
            # 9. Get the bytes of the H264 encoded frame
            frame_bytes = bytes(packet_1.imgFrame.getData())
            # 10. Get a timestamp (doesn't have to be super precise, but should be increasing or at least non-decreasing)
            timestamp = int(time.time() * 1_000)
            # 11. Use our StreamHandle object to send the whole package to the Agent.  
            person_detection_stream_handle.publish_video_data(frame_bytes, timestamp, metadata)
        
        # 12. Use depthai_sdk's OakCamera.sync method to synchronize the encoded stream output and detection-NN output and add the callback to this synced output.
        self.oak.sync([det.out.main, camera.out.encoded], callback = detection_cb)
