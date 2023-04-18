import robothub
from robothub_oak import DEVICE_MANAGER
from threading import Event

class ObjectDetection(robothub.RobotHubApplication):
    def on_start(self):
        # Get first connected device
        device = DEVICE_MANAGER.get_all_devices()[0]
        
        # Create a YoloV6 object detection NN with color sensor as input 
        color = device.get_camera('color', resolution='1080p', fps=22)   
        nn = device.create_neural_network('yolov6nr3_coco_640x352', color)
        nn.stream_to_hub(name=f'Object Detection Stream', unique_key='nn_stream')
        stereo = device.get_stereo_camera(resolution='800p', fps=30)
        stereo.stream_to_hub(name=f'Depth Stream')
            
    def start_execution(self):
        DEVICE_MANAGER.start()

    def on_stop(self):
        DEVICE_MANAGER.stop()
