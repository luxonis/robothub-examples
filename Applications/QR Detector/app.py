import cv2
import depthai
import numpy as np

from pathlib import Path


# ---------------------
#  PIPELINE DEFINITION
# ---------------------
# pipeline object
pipeline = depthai.Pipeline()


# NODES
# ColorCamera
# https://docs.luxonis.com/projects/api/en/latest/components/nodes/color_camera/
cam = pipeline.create(depthai.node.ColorCamera)
cam.setResolution(depthai.ColorCameraProperties.SensorResolution.THE_1080_P)

# Script
# https://docs.luxonis.com/projects/api/en/latest/components/nodes/script/
script = pipeline.create(depthai.node.Script)
# split the image from the camera into 9 tiles, save the values to a config and send it
# to the ImageManip together with the image to handle the actual cropping and resizing
script.setScript("""
    NN_INPUT_SIZE_W = 512
    NN_INPUT_SIZE_H = 288
                 
    crop_vals = [(0.0, 0.0), (0.0, 0.3), (0.0, 0.6), (0.3, 0.0), (0.3, 0.3), (0.3, 0.6), (0.6, 0.0), (0.6, 0.3), (0.6, 0.6)]
    
    step = 0.4
                 
    while True:
        frame = node.io['in_still'].tryGet()
                 
        if frame is not None:
            for val in crop_vals:
                xmin = val[0]
                ymin = val[1]
                xmax = xmin + step
                ymax = ymin + step
                 
                config = ImageManipConfig()
                config.setFrameType(ImgFrame.Type.BGR888p)
                config.setCropRect(xmin, ymin, xmax, ymax)
                config.setResize(NN_INPUT_SIZE_W, NN_INPUT_SIZE_H)
                
                node.io['out_cfg'].send(config)
                node.io['out_still'].send(frame)
""")

# ImageManip
# https://docs.luxonis.com/projects/api/en/latest/components/nodes/image_manip/
manip = pipeline.create(depthai.node.ImageManip)
manip.inputConfig.setWaitForMessage(True)   # wait for both config and image

# YoloDetectionNetwork
# https://docs.luxonis.com/projects/api/en/latest/components/nodes/yolo_detection_network/
nn_yolo = pipeline.create(depthai.node.YoloDetectionNetwork)
nn_yolo.setBlobPath(str((Path(__file__).parent / Path('qr_model_512x288_rvc2_openvino_2022.1_6shave.blob')).resolve().absolute()))
nn_yolo.setConfidenceThreshold(0.1)
nn_yolo.setNumClasses(1)
nn_yolo.setCoordinateSize(4)
nn_yolo.setIouThreshold(0.5)
nn_yolo.setNumInferenceThreads(2)
nn_yolo.input.setBlocking(False)

# XLinkIn (camera control)
# https://docs.luxonis.com/projects/api/en/latest/components/nodes/xlink_in/
cam_control = pipeline.create(depthai.node.XLinkIn)
cam_control.setStreamName("cam_control")

# XLinkOut (camera video)
# https://docs.luxonis.com/projects/api/en/latest/components/nodes/xlink_out/
xout_video = pipeline.create(depthai.node.XLinkOut)
xout_video.setStreamName("video")

# XLinkOut (camera still image)
# https://docs.luxonis.com/projects/api/en/latest/components/nodes/xlink_out/
xout_still = pipeline.create(depthai.node.XLinkOut)
xout_still.setStreamName("still")

# XLinkOut (image manip cropped images)
# https://docs.luxonis.com/projects/api/en/latest/components/nodes/xlink_out/
xout_crop = pipeline.create(depthai.node.XLinkOut)
xout_crop.setStreamName("crop")

# XLinkOut (NN output)
# https://docs.luxonis.com/projects/api/en/latest/components/nodes/xlink_out/
xout_nn = pipeline.create(depthai.node.XLinkOut)
xout_nn.setStreamName("nn")


# LINKS
# camera control -> camera
cam_control.out.link(cam.inputControl)

# camera (video) -> host
cam.video.link(xout_video.input)
# camera (still) -> host
cam.still.link(xout_still.input)
# camera (still) -> script
cam.still.link(script.inputs['in_still'])

# script -> image manip (config)
script.outputs['out_cfg'].link(manip.inputConfig)
# script -> image manip (frame)
script.outputs['out_still'].link(manip.inputImage)

# image manip -> NN
manip.out.link(nn_yolo.input)

# NN -> out (host)
nn_yolo.out.link(xout_nn.input)  # detections
nn_yolo.passthrough.link(xout_crop.input)   # input image


# ------------------
#  RUN THE PIPELINE
# ------------------
with depthai.Device(pipeline) as device:
    # host-side output queues to access the produced results
    controlQueue = device.getInputQueue("cam_control")
    videoQueue = device.getOutputQueue("video")
    stillQueue = device.getOutputQueue("still")
    cropQueue = device.getOutputQueue("crop")
    nnQueue = device.getOutputQueue("nn")

    
    # TODO: bound "scale" and "mean" to the number of cropped images

    crop_vals = [(0.0, 0.0), (0.0, 0.3), (0.0, 0.6), (0.3, 0.0), (0.3, 0.3), (0.3, 0.6), (0.6, 0.0), (0.6, 0.3), (0.6, 0.6)]
    CROP_FACTOR = 0.4   # corresponds to "step" in the Script node
    NUMBER_OF_CROPPED_IMAGES = 9    # corresponds to the number of cropped images created by the Script node
    
    
    # scale_factor can be scalar (= same for both x,y) or vector [scale_x, scale_y]
    def wh_from_frame(frame, scale_factor = 1):
        wh = np.flip(frame.shape[0:-1])     # order of coordinates: x, y (width, height)
        return wh * np.array(scale_factor)


    # coordinates order - x, y
    def transform_coords(coords_from, coords_to, bbox, mean = 0):
        # calculate scale values for the given coordinates combination and extend the resulting vector
        # to match the dimensions of the bounding box (xmin, ymin, xmax, ymax),
        # i.e., [x_s, y_s] -> [x_s, y_s, x_s, y_s]
        S = coords_to / coords_from
        S = np.tile(S, 2)
        
        M = np.array(mean)
        # if M is a vector, extend it to match the dimensions of the bounding box (xmin, ymin, xmax, ymax),
        # i.e., [x_m, y_m] -> [x_m, y_m, x_m, y_m].
        # There is no need to do this if M is a scalar.
        if np.ndim(M) > 0:
            M = np.tile(M, 2)  

        return (bbox * S + M).astype(int)


    
    color_red = (0, 0, 255)
    # color_green = (0, 255, 0)
    # color_blue = (255, 0, 0)

    yolo_frame = None
    detections = []

    while True:
        # process video input from camera (if any)
        vidFrames = videoQueue.tryGetAll()
        for vidFrame in vidFrames:
            cv2.imshow("Video", vidFrame.getCvFrame())

        # process image input from camera (if any)
        if cropQueue.has() and nnQueue.has() and stillQueue.has():
            still_frame = stillQueue.get().getCvFrame()

            bboxes = []
            confidences = []

            # if any QR codes were detected, display the image and highlight the codes with rectangles.
            # If not, just display the image.

            # process results from all cropped images
            for i in range(NUMBER_OF_CROPPED_IMAGES):
                # get the cropped image + the corresponding detections
                yolo_frame = cropQueue.get().getCvFrame()
                detections = nnQueue.get().detections

                # calculate coordinates of each detection wrt the original frame
                for detection in detections:
                    # transform the bounding box from the detections space <0..1> to the yolo_frame space
                    bbox_detection = (detection.xmin, detection.ymin, detection.xmax, detection.ymax)
                    bbox_yolo_frame = transform_coords(np.array([1,1]), wh_from_frame(yolo_frame), bbox_detection)
                    
                    # transform the bounding box from the yolo_frame space to the coordinates in the original image
                    bbox = transform_coords(wh_from_frame(yolo_frame), wh_from_frame(still_frame, CROP_FACTOR), bbox_yolo_frame, wh_from_frame(still_frame, crop_vals[i]))

                    # save the final bounding box and confidence of the detection
                    bboxes.append(bbox.tolist())
                    confidences.append(detection.confidence)
                    
            # calculate NMS over all detected bounding boxes
            confidence_threshold = 0.1  # generally should match yolo's confidence_threshold
            overlap_threshold = 0.01
            nmsboxes = [(bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1]) for bbox in bboxes]
            indices = cv2.dnn.NMSBoxes(nmsboxes, confidences, confidence_threshold, overlap_threshold)
            
            # display and print info about each resulting bounding box
            for index in indices:
                bbox = bboxes[index]
                cv2.rectangle(still_frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color_red, 2)
                cv2.putText(still_frame, f"{int(confidences[index] * 100)}%", (bbox[0] + 10, bbox[1] + 40), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color_red)

                print(f"QR code detected: coordinates: {bbox}, confidence: {confidences[index] * 100:.2f}%")            

            # display the original frame
            cv2.imshow("Still", still_frame)
        

        # keyboard controls
        key = cv2.waitKey(1)
        # terminate the program when "q" is pressed
        if key == ord("q"):
            break
        # create a screenshot when "c" is pressed
        elif key == ord("c"):
            ctrl = depthai.CameraControl()
            ctrl.setCaptureStill(True)
            controlQueue.send(ctrl)
