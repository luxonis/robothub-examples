from robothub_oak.manager import DEVICE_MANAGER
from robothub_oak import Device
import traceback
import robothub
import uuid
import time

class CameraApp(robothub.RobotHubApplication):
    def _sensor_resolutions(self, device) -> dict[str, list[str]]:
        def sensor_resolutions(sensor: str):
            return {
            'IMX214':  ['1080p', '2160p'],#, '12mp'],
            'IMX378':  ['1080p', '2160p'],#, '12mp'],
            'IMX577':  ['12mp'],
            'IMX582':  ['2160p'],#, '12mp', '32mp'],
            'OV9282':  ['400p', '720p', '800p'],
            'OV7251':  ['400p', '480p'],
            'AR0234':  ['1200p'],
            'LCM48':   ['2160p'],
            }.get(sensor, ['1080p'])

        cameras = device.getCameraSensorNames()

        deviceResolutions = {
            'color': [],
            'mono': []
        }

        for socket, sensor in cameras.items():
            if socket == socket.RGB:
                deviceResolutions['color'] = sensor_resolutions(sensor)
            elif socket in [socket.LEFT, socket.RIGHT]:
                deviceResolutions['mono'] = sensor_resolutions(sensor)
            
        return deviceResolutions

    def _stream_type(self, stream: str) -> str:
        if stream == 'color':
            return 'color'
        return 'mono'

    def _overlay_active(self, device, stream):
        if stream == 'color':
            return device.conf['detections']
        return device.conf['colormap']
    
    def _order_first(self, element, original):
        if not element in original:
            return original
        array = original.copy()
        array.remove(element)
        array.insert(0, element)
        return array

    def setup_device(self, device: Device, **kwargs):
        device.reset()
        print("setup")


        if not hasattr(device, 'conf'):
            device.conf = {
                'colormap': True,
                'detections': False,
                'temporal-filter': False,
                'ir-strength': 850
            }
            device.streams = {
                'top': 'color',
                'bot': 'stereo'
            }
            device.resolutions = {
                'color': '1080p',
                'mono': '400p'
            }

        if kwargs.get('top', None) != None: device.streams['top'] = kwargs['top']
        if kwargs.get('bot', None) != None: device.streams['bot'] = kwargs['bot']
        if kwargs.get('color', None) != None: device.resolutions['color'] = kwargs['color']
        if kwargs.get('mono', None) != None: device.resolutions['mono'] = kwargs['mono']
        
        print(f'Setting up device {device.get_device_name()} with {device.streams} and {device.resolutions}')
        def on_connected(hubCam):
            print(f"{hubCam.device_name} {hubCam.device.getMxId()} connected")
            robothub.COMMUNICATOR.notify(str(uuid.uuid4()), {'status': 'running', 'deviceId': hubCam.device.getMxId()})
        device.connect_callback = on_connected

        color = device.get_camera('color', resolution=device.resolutions['color'], fps=30)
        left = device.get_camera('left', resolution=device.resolutions['mono'], fps=30)
        right = device.get_camera('right', resolution=device.resolutions['mono'], fps=30)
        stereo = device.get_stereo_camera(resolution=device.resolutions['mono'], fps=30, left_camera=left, right_camera=right)
        stereo.configure(align=color)
        color.configure(isp_scale=(1,3))

        if 'color' in device.streams.values():
            color.stream_to_hub(name=f'Color stream {device.mxid}', unique_key=f'color-stream/{device.mxid}')
            nn = device.create_neural_network('mobilenet-ssd', color)
            nn.stream_to_hub(name=f'NN stream {device.mxid}', unique_key=f'nn-stream/{device.mxid}')

        if 'left' in device.streams.values():
            left.stream_to_hub(name=f'Left stream {device.mxid}', unique_key=f'left-stream/{device.mxid}')

        if 'right' in device.streams.values():
            right.stream_to_hub(name=f'Right stream {device.mxid}', unique_key=f'right-stream/{device.mxid}')
        
        if 'stereo' in device.streams.values():
            stereo.stream_to_hub(name=f'Stereo stream {device.mxid}', unique_key=f'stereo-stream/{device.mxid}')
            device.spatialLocation = device.get_spatial_location_calculator(stereo)
            device.stereoControl = device.get_stereo_control(stereo)

       
        time.sleep(0.1) # Sleep to prevent duplicate stream error


    def on_start(self):
        devices = DEVICE_MANAGER.get_all_devices()

        for device in devices:
            self.setup_device(device)

        robothub.COMMUNICATOR.on_frontend(notification=self.on_fe_notification, request=self.on_fe_request)

    def on_fe_request(self, session_id, unique_key, payload):
        try:
            print(f'FEReq: {unique_key} {payload}')
            if unique_key == 'get':
                if payload['option'] == 'devices':
                     return [{
                        'name': dev.oak['productName'],
                        'mxid': dev.oak['serialNumber']} for dev in robothub.DEVICES
                    ]
                elif payload['option'] == 'config':
                    device = DEVICE_MANAGER.get_device(payload['deviceId'])

                    hubCam = device.hub_camera

                    if hubCam is None:
                        return [{'id': 'camera', 'data': [{'name': 'Searching for cameras'}]}]
                    if hubCam.device is None:
                        return [{'id': 'camera', 'data': [{'name': 'Searching for cameras'}]}]
                                        
                    supportedResolutions = self._sensor_resolutions(hubCam.device)

                    supportedSterams = []

                    if hubCam.has_color: supportedSterams.append('color')
                    if hubCam.has_left: supportedSterams.append('left')
                    if hubCam.has_right: supportedSterams.append('right')
                    if hubCam.has_stereo: supportedSterams.append('stereo')

                    topStream = self._stream_type(device.streams['top'])
                    botStream = self._stream_type(device.streams['bot'])
                    topResolution = device.resolutions[topStream]
                    botResolution = device.resolutions[botStream]

                    return [
                        {'id': 'ir-strength',           'data': device.conf['ir-strength']},
                        {'id': 'temporal-filter',       'data': device.conf['temporal-filter']},
                        {'id': 'top-stream',            'data': self._order_first(device.streams['top'], supportedSterams)},
                        {'id': 'top-resolution',        'data': self._order_first(topResolution, supportedResolutions[topStream])},
                        {'id': 'top-overlay',           'data': self._overlay_active(device, topStream)},
                        {'id': 'bot-stream',            'data': self._order_first(device.streams['bot'], supportedSterams)},
                        {'id': 'bot-resolution',        'data': self._order_first(botResolution, supportedResolutions[botStream])},
                        {'id': 'bot-overlay',           'data': self._overlay_active(device, botStream)},
                    ]
                elif payload['option'] == 'resolutions':
                    device = DEVICE_MANAGER.get_device(payload['deviceId'])

                    hubCam = device.hub_camera

                    if hubCam is None:
                        return [{'id': 'camera', 'data': [{'name': 'Searching for cameras'}]}]
                    if hubCam.device is None:
                        return [{'id': 'camera', 'data': [{'name': 'Searching for cameras'}]}]
                    
                    supportedResolutions = self._sensor_resolutions(hubCam.device)

                    return {
                        'color': self._order_first(device.resolutions['color'], supportedResolutions['color']),
                        'mono': self._order_first(device.resolutions['mono'], supportedResolutions['mono'])
                    }
                elif payload['option'] == 'depth':
                    device = DEVICE_MANAGER.get_device(payload['deviceId'])
                    if device is None:
                        return
                    return device.spatialLocation.get_location()
            elif unique_key == 'ping':
                return 'pong'
        except Exception as e:
            traceback.print_exception(e)
            return {'error': f'{e}'}


    def on_fe_notification(self, session_id, unique_key, payload):
        try:
            print(f'FENtf: {unique_key} {payload}')
            device = DEVICE_MANAGER.get_device(payload['deviceId'])
            if device is None or device.hub_camera is None or device.hub_camera.oak_camera is None:
                return
            
            if unique_key == 'set':
                if payload['option'][3:] == '-resolution':
                    channel = payload['option'][:3]
                    if device.resolutions[self._stream_type(device.streams[channel])] != payload['value']:
                        self.setup_device(device, **{self._stream_type(device.streams[channel]): payload['value']})
                        device.restart()

                elif payload['option'][3:] == '-stream':
                    channel = payload['option'][:3]
                    if device.streams[channel] != payload['value']:
                        self.setup_device(device, **{channel: payload['value']})
                        device.restart()
                elif payload['option'] == 'depth-query':
                    pos = payload['value']
                    x, y = int(max(0, min(629, pos['x'] * 640))), int(max(0, min(349, pos['y'] * 360)))
                    device.spatialLocation.set_roi((x, y), (10, 10))
                elif payload['option'] == 'temporal-filter':
                    device.stereoControl.send_controls({'algorithm_control': {'align': 'CENTER'}, 'postprocessing': {"temporal": {"enable": payload['value']}}})
                    device.conf['temporal-filter'] = payload['value']
                elif payload['option'] == 'ir-strength':
                    device.hub_camera.device.setIrLaserDotProjectorBrightness(int(payload['value']))
                    device.conf['ir-strength'] = payload['value']
                elif payload['option'] == 'colormap':
                    device.stereoControl.send_colormap_controls({'colormap': 'JET' if payload['value'] else 'NONE'})
                    device.conf['colormap'] = payload['value']
                elif payload['option'] == 'detections':
                    device.conf['detections'] = payload['value']

        except Exception as e:
            traceback.print_exception(e)

    def start_execution(self):
        DEVICE_MANAGER.start()

    def on_stop(self):
        DEVICE_MANAGER.stop()