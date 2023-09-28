import time

import depthai as dai
import numpy as np
import robothub_core


class ObjectDetection(robothub_core.RobotHubApplication):
    def on_start(self):
        fps = robothub_core.CONFIGURATION['det_fps']
        print(f'FPS set to {fps}, connecting to devices...')

        # connect to the device(s), build pipeline and upload it to the device
        self.connect(fps)

        # create polling thread and start it
        run_polling_thread = robothub_core.threading.Thread(target=self.polling_thread, name="PollingThread",
                                                            daemon=False)
        run_polling_thread.start()

    def connect(self, fps):
        self.devices = dict()
        self.streams = dict()
        self.outQueues = dict()

        for device in robothub_core.DEVICES:
            mxid = device.oak["serialNumber"]
            device_name = device.oak['productName']

            start_time = time.time()
            give_up_time = start_time + 10
            cameras = None
            while time.time() < give_up_time and self.running:
                try:
                    self.devices[mxid] = dai.Device(mxid)
                    cameras = self.devices[mxid].getConnectedCameras()
                    print(f'Connected device "{device_name}" with sensors: {cameras}')
                    break
                except RuntimeError as e:
                    # If device can't be connected to on first try, wait 0.1 seconds and try again. 
                    print(f"Error while trying to connect {device_name}: {e}")
                    self.wait(0.1)
                    continue
            if cameras is not None:
                pipeline, out_queues = self.build_pipeline(mxid, fps)
                self.devices[mxid].startPipeline(pipeline)
                self.devices[mxid].setIrLaserDotProjectorBrightness(1200)
                self.streams['color'] = robothub_core.STREAMS.create_video(mxid, f'stream_{mxid}_color',
                                                                           f'{device_name} - Object Detection Stream')
                self.streams['depth'] = robothub_core.STREAMS.create_video(mxid, f'stream_{mxid}_depth',
                                                                           f'{device_name} - Depth Stream')
                for name in out_queues:
                    self.outQueues[name] = self.devices[mxid].getOutputQueue(name=name, maxSize=4, blocking=False)
                print(f'Device "{device_name}": Started 1080p Object Detection & Depth Streams')
            else:
                raise Exception(f'Could not start device {device_name}: No cameras found')

    def polling_thread(self):
        # Create polling thread
        self.detections = []
        while self.running:
            self.process_output()
            self.wait(0.0001)

    def build_pipeline(self, mxid, fps) -> [dai.Pipeline, list[str]]:
        pipeline = dai.Pipeline()

        # Color camera
        camRgb = pipeline.createColorCamera()
        camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
        camRgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.RGB)
        camRgb.setPreviewSize(640, 640)
        camRgb.setInterleaved(False)
        camRgb.setFps(fps)

        # Left camera output
        left = pipeline.createMonoCamera()
        left.setBoardSocket(dai.CameraBoardSocket.LEFT)
        left.setResolution(dai.MonoCameraProperties.SensorResolution.THE_800_P)
        left.setFps(fps)

        # Right camera output
        right = pipeline.createMonoCamera()
        right.setBoardSocket(dai.CameraBoardSocket.RIGHT)
        right.setResolution(dai.MonoCameraProperties.SensorResolution.THE_800_P)
        right.setFps(fps)

        # Stereo
        stereo = pipeline.createStereoDepth()
        stereo.setDepthAlign(dai.CameraBoardSocket.RGB)
        left.out.link(stereo.left)
        right.out.link(stereo.right)

        # Stereo settings
        stereo.initialConfig.setMedianFilter(dai.MedianFilter.KERNEL_5x5)
        stereo.initialConfig.setLeftRightCheck(True)
        # stereo.initialConfig.setSubpixel(True)
        config = stereo.initialConfig.get()
        config.postProcessing.decimationFilter.decimationFactor = 1
        config.postProcessing.speckleFilter.enable = False
        config.postProcessing.speckleFilter.speckleRange = 50
        config.postProcessing.temporalFilter.enable = True
        config.postProcessing.thresholdFilter.minRange = 400
        config.postProcessing.thresholdFilter.maxRange = 15000
        # config.postProcessing.spatialFilter.enable = True
        # config.postProcessing.spatialFilter.holeFillingRadius = 2
        # config.postProcessing.spatialFilter.numIterations = 1
        stereo.initialConfig.set(config)

        colormap = pipeline.createImageManip()
        colormap.initialConfig.setColormap(dai.Colormap.JET, stereo.initialConfig.getMaxDisparity())
        colormap.initialConfig.setFrameType(dai.ImgFrame.Type.NV12)
        colormap.setMaxOutputFrameSize(3110400)
        stereo.disparity.link(colormap.inputImage)

        # Yolo network
        detectionNetwork = pipeline.createYoloDetectionNetwork()
        detectionNetwork.setBlobPath(model_path)
        detectionNetwork.setConfidenceThreshold(0.5)
        detectionNetwork.setNumClasses(80)
        detectionNetwork.setCoordinateSize(4)
        detectionNetwork.setIouThreshold(0.5)

        detectionNetwork.setNumInferenceThreads(2)
        detectionNetwork.input.setBlocking(False)

        color_encoder = pipeline.createVideoEncoder()
        stereo_encoder = pipeline.createVideoEncoder()

        color_encoder.setDefaultProfilePreset(fps, dai.VideoEncoderProperties.Profile.H264_MAIN)
        stereo_encoder.setDefaultProfilePreset(fps, dai.VideoEncoderProperties.Profile.H264_MAIN)

        # Outputs
        encoded_depth_out = pipeline.create(dai.node.XLinkOut)
        encoded_rgb_out = pipeline.create(dai.node.XLinkOut)
        yolo_out = pipeline.create(dai.node.XLinkOut)

        encoded_depth_out.setStreamName("Depth")
        encoded_rgb_out.setStreamName("Color")
        yolo_out.setStreamName("Yolo")

        # Linking
        colormap.out.link(stereo_encoder.input)
        camRgb.video.link(color_encoder.input)
        camRgb.preview.link(detectionNetwork.input)

        # Link to output streams
        detectionNetwork.out.link(yolo_out.input)
        stereo_encoder.bitstream.link(encoded_depth_out.input)
        color_encoder.bitstream.link(encoded_rgb_out.input)

        out_queue_names = ["Depth", "Color", "Yolo"]

        return pipeline, out_queue_names

    def frameNorm(self, bbox):
        normVals = np.full(len(bbox), 1080)
        normVals[::2] = 1080
        return (np.clip(np.array(bbox), 0, 1) * normVals).astype(int)

    def process_output(self):
        inRgb = self.outQueues['Color'].tryGet()
        inDepth = self.outQueues['Depth'].tryGet()
        inDet = self.outQueues['Yolo'].tryGet()
        if inDet:
            self.detections = inDet.detections
        if inRgb:
            frame_bytes = bytes(inRgb.getFrame())
            timestamp = int(time.time() * 1_000)
            if len(self.detections) > 0:
                detections_metadata = []
                for detection in self.detections:
                    label = labelMap[detection.label]
                    capitalized_label = label[0:1].upper() + label[1:]
                    unnormed_bbox = [detection.xmin, detection.ymin, detection.xmax, detection.ymax]
                    np_bbox = self.frameNorm([detection.xmin, detection.ymin, detection.xmax, detection.ymax])
                    bbox = [420 + int(np_bbox[0]), int(np_bbox[1]), 420 + int(np_bbox[2]), int(np_bbox[3])]
                    detections_metadata.append({
                        'bbox': bbox,
                        'label': capitalized_label,
                        'color': [0, 242, 255],
                    })
                metadata = {
                    'platform': 'robothub',
                    'frame_shape': [1920, 1080, 3],
                    'config': {
                        'detection': {
                            'thickness': 1,
                            'fill_transparency': 0.15,
                            'box_roundness': 1,
                            'color': [0, 242, 255],
                        },
                        'text': {
                            'font_color': [0, 242, 255],
                            'font_transparency': 0.5,
                            'font_scale': 1.0,
                            'font_thickness': 2,
                            'bg_transparency': 0.5,
                            'bg_color': [208, 239, 255],
                        },
                    },
                    'objects': [
                        {
                            'type': 'detections',
                            'detections': detections_metadata
                        }
                    ]
                }
            else:
                metadata = None
            self.streams['color'].publish_video_data(frame_bytes, timestamp, metadata)
        if inDepth:
            frame_bytes = bytes(inDepth.getFrame())
            timestamp = int(time.time() * 1_000)
            self.streams['depth'].publish_video_data(frame_bytes, timestamp, None)

    def on_stop(self):
        print('Stopping App')
        try:
            self.run_polling_thread.join()
        except BaseException as e:
            pass
        try:
            robothub_core.STREAMS.destroy_all_streams()
        except BaseException as e:
            pass


model_path = '/app/yolo_v6.blob'

labelMap = [
    "person",
    "bicycle",
    "car",
    "motorbike",
    "aeroplane",
    "bus",
    "train",
    "truck",
    "boat",
    "traffic light",
    "fire hydrant",
    "stop sign",
    "parking meter",
    "bench",
    "bird",
    "cat",
    "dog",
    "horse",
    "sheep",
    "cow",
    "elephant",
    "bear",
    "zebra",
    "giraffe",
    "backpack",
    "umbrella",
    "handbag",
    "tie",
    "suitcase",
    "frisbee",
    "skis",
    "snowboard",
    "sports ball",
    "kite",
    "baseball bat",
    "baseball glove",
    "skateboard",
    "surfboard",
    "tennis racket",
    "bottle",
    "wine glass",
    "cup",
    "fork",
    "knife",
    "spoon",
    "bowl",
    "banana",
    "apple",
    "sandwich",
    "orange",
    "broccoli",
    "carrot",
    "hot dog",
    "pizza",
    "donut",
    "cake",
    "chair",
    "sofa",
    "pottedplant",
    "bed",
    "diningtable",
    "toilet",
    "tvmonitor",
    "laptop",
    "mouse",
    "remote",
    "keyboard",
    "cell phone",
    "microwave",
    "oven",
    "toaster",
    "sink",
    "refrigerator",
    "book",
    "clock",
    "vase",
    "scissors",
    "teddy bear",
    "hair drier",
    "toothbrush"
]
