import time
import logging as log
import os
import contextlib
from depthai_sdk import OakCamera, FramePacket
import numpy as np
import cv2
import depthai as dai

class ExampleApplication(robothub.RobotHubApplication):
    def on_start(self):
        # This is the entrypoint of your App. 
        # It should be used:
        #   - As a constructor for your App
        #   - To connect/initialize devices, download blobs if needed, initialize streams
        # on_start() must terminate
        # If on_start() excepts, agent will restart the app

        # In this App, we will log Machine ID and Name of the first available device (from robothub.DEVICES, which contains all devices assigned to the app)
        assigned_id = robothub.DEVICES[0].oak.get('serialNumber')
        log.info(f'Assigned device: {assigned_id}')
        config = robothub.CONFIGURATION
        # Then we will log loaded configuration
        log.info(f'Configuration: {config}')

        # Then we will connect to the device with DepthAI
        self.dai_device = DaiDevice(self, assigned_id)      
        # Use a method to get device name and connected sensors
        self.dai_device.get_device_info()
        log.info(f'Device {self.dai_device.device_name} connected, detected sensors: {str(self.dai_device.cameras)}')

        # And initialize the person detection stream
        self.dai_device.initialize_detection()
        log.info('Starting person detection...')

        # Initialize a thread to poll the device -> As in depthai_sdk, polling the device automatically calls callbacks
        self.run_polling_thread = robothub.threading.Thread(target = self.polling_thread, name="PollingThread", daemon=False)

        # Initialize a report thread
        self.run_report_thread  = robothub.threading.Thread(target = self.report_thread, name="ReportThread", daemon=False)

        # Start the device and run the polling and report thread
        self.dai_device.start()
        self.run_report_thread.start()
        self.run_polling_thread.start()
        
    def report_thread(self):
        while self.running:
            self.report()

    def report(self):
        # This is callback which will report device info & stats to the cloud. It needs to include a self.wait() for performance reasons.
        device_info = self.dai_device._device_info_report()
        device_stats = self.dai_device._device_stats_report()
        robothub.AGENT.publish_device_info(device_info)
        robothub.AGENT.publish_device_stats(device_stats)
        self.wait(2)
    
    def polling_thread(self):
        # Periodically polls the device, indirectly calling self.dai_device.detection_cb() defined on line 263 which sends detections to RobotHub
        log.debug('Starting device polling loop')
        while self.running:
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
            self.dai_device.detection_thread.join()
        except:
            log.info(dir(self.dai_device))
            log.debug('Detection thread join excepted with {e}')
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
        self.config = robothub.CONFIGURATION

    def start(self, reattempt_time = 1) -> None:
        # Uses the depthai_sdk to load a pipeline to a connected device
        log.debug('starting')
        while self.app.running:
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

    def send_frame_detection(self, frame: dai.ImgFrame, title: str, device_id: str):

        cv_frame = frame.getCvFrame()
        detection = robothub.DETECTIONS.prepare()
        detection.add_frame(bytes(cv_frame), device_id)
        detection.set_title(title)
        robothub.DETECTIONS.upload(detection)
        time.sleep(10)


    def initialize_detection(self, resolution = '400p', fps = 30) -> None:

        # 1. Some safety checks
        if len(self.cameras.keys()) == 0:
            raise Exception('Cannot initialize detection with no sensors')
        color = False
        for camera_ in self.cameras.keys():
            if camera_.name.upper() == 'RGB':
                color = True
        if color == False:
            raise Exception('Cannot initialize person detection, no sensor supports RGB')

        log.debug('starting detection')

        # 2. create a pipeline through depthai_sdk 
        camera = self.oak.create_camera('color', resolution = resolution, fps=fps, encode='h264')
        # 3. get parameters of the color sensor
        width = camera.node.getResolutionWidth()
        height = camera.node.getResolutionHeight()

        # 4. Add a neural network for person detection to the same pipeline and configure it
        det = self.oak.create_nn('person-detection-retail-0013', camera, nn_type='mobilenet')
        log.info(self.config.keys())
        conf_threshold = self.config['nn_threshold']
        det.config_nn(conf_threshold=conf_threshold)
        # 5. Define a callback for outputs of the pipeline
        def detection_cb(packet):
            packet_1 = packet['1_bitstream']            
            decoded_image = packet_1.frame
            _, jpeg = cv2.imencode('.jpeg', decoded_image)
            new_frame = dai.ImgFrame()
            new_frame.setData(jpeg)
            new_frame.setWidth(width)
            new_frame.setHeight(height)
            new_frame.setType(dai.ImgFrame.Type.BITSTREAM)
            self.detection_thread = robothub.threading.Thread(target=self.send_frame_detection, name="detection_thread", daemon=True, args=(new_frame, 'person', self.id))
            self.detection_thread.start()


        # 6. Use depthai_sdk's OakCamera.sync method to synchronize the encoded detection pictures and detection-NN output and add the callback to this synced output.
        self.oak.sync([det.out.main, camera.out.encoded], callback = detection_cb)
