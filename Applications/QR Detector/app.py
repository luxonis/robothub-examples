import cv2
import depthai
import numpy as np
import time

from pathlib import Path


NN_INPUT_SIZE_W = 512
NN_INPUT_SIZE_H = 288


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
cam.setPreviewSize(960,540)     # (1920,1080) / 2

# Script
# https://docs.luxonis.com/projects/api/en/latest/components/nodes/script/
script = pipeline.create(depthai.node.Script)
# split the image from the camera into 9 tiles, save the values to a config and send it
# to the ImageManip together with the image to handle the actual cropping and resizing
script.setScript("""
    import time

    NN_INPUT_SIZE_W = 512
    NN_INPUT_SIZE_H = 288
                 
    crop_vals = [(0.0, 0.0), (0.0, 0.3), (0.0, 0.6), (0.3, 0.0), (0.3, 0.3), (0.3, 0.6), (0.6, 0.0), (0.6, 0.3), (0.6, 0.6)]
    
    step = 0.4
                 
    while True:
        time_report = {}
        start = time.perf_counter()
        frame = node.io['in_preview'].get()
        time_report['img'] = time.perf_counter() - start

        start_loop = time.perf_counter()
        time_report['dets'] = []
        for val in crop_vals:
            start_det = time.perf_counter()
            xmin = val[0]
            ymin = val[1]
            xmax = xmin + step
            ymax = ymin + step

            config = ImageManipConfig()
            config.setFrameType(ImgFrame.Type.BGR888p)
            config.setCropRect(xmin, ymin, xmax, ymax)
            config.setResize(NN_INPUT_SIZE_W, NN_INPUT_SIZE_H)

            node.io['out_cfg'].send(config)
            node.io['out_frame'].send(frame)
            time_report['dets'].append(time.perf_counter() - start_det)
        time_report['det_loop'] = time.perf_counter() - start_loop

        min_, max_, sum_ = None, None, 0.
        for i, det in enumerate(time_report['dets']):
            if min_ is None or det < min_[0]:
                min_ = (det, i)
            if max_ is None or det > max_[0]:
                max_ = (det, i)
            sum_ += det
        node.warn(
            f"img: {time_report['img']:.5f}, "
            f"dets: ("
            f"loop: {time_report['det_loop']:.5f}, "
            f"avg: {sum_ / 9.:.5f}, "
            f"min: ({min_[0]:.5f}, {min_[1]})"
            f"max: ({max_[0]:.5f}, {max_[1]})"
            f")"
        )
""")

script.inputs["in_preview"].setBlocking(True)  # for safe measure
# always set queue size 1, if you can - in this case, if script node is slower than the fps, there is no use
# for sending another images to the script node
script.inputs["in_preview"].setQueueSize(1)

# ImageManip
# https://docs.luxonis.com/projects/api/en/latest/components/nodes/image_manip/
manip = pipeline.create(depthai.node.ImageManip)
manip.inputConfig.setWaitForMessage(True)   # wait for both config and image
# above you say the setWaitForMessage includes also waiting for image - might be true, but in my experience,
# it's never a bad practice to set these explicitly, since you at least know exactly what is set (default values are hard to find in the doc)
manip.inputImage.setWaitForMessage(True)
manip.inputConfig.setBlocking(True)  # set blocking, otherwise configs in queue might be overwritten
manip.inputImage.setBlocking(True)  # set blocking, otherwise configs in queue might be overwritten
manip.inputConfig.setQueueSize(1)
manip.inputImage.setQueueSize(1)
manip.setMaxOutputFrameSize(NN_INPUT_SIZE_W * NN_INPUT_SIZE_H * 3)  # just to be sure you know what's actually output

# YoloDetectionNetwork
# https://docs.luxonis.com/projects/api/en/latest/components/nodes/yolo_detection_network/
nn_yolo = pipeline.create(depthai.node.YoloDetectionNetwork)
nn_yolo.setBlobPath(str((Path(__file__).parent / Path('qr_model_512x288_rvc2_openvino_2022.1_6shave.blob')).resolve().absolute()))
nn_yolo.setConfidenceThreshold(0.1)
nn_yolo.setNumClasses(1)
nn_yolo.setCoordinateSize(4)
nn_yolo.setIouThreshold(0.5)
nn_yolo.setNumInferenceThreads(2)
nn_yolo.input.setBlocking(True)  # set blocking, otherwise configs in queue might be overwritten
nn_yolo.input.setQueueSize(50)  # it can keep all the crops in a queue and unblock the image manip, that would be stuck on image.send()

# XLinkOut (camera video)
# https://docs.luxonis.com/projects/api/en/latest/components/nodes/xlink_out/
xout_video = pipeline.create(depthai.node.XLinkOut)
xout_video.setStreamName("video")

# XLinkOut (NN output)
# https://docs.luxonis.com/projects/api/en/latest/components/nodes/xlink_out/
xout_nn = pipeline.create(depthai.node.XLinkOut)
xout_nn.setStreamName("nn")


# LINKS
# camera (preview) -> script
cam.preview.link(script.inputs['in_preview'])
# camera (preview) -> host
cam.preview.link(xout_video.input)

# script -> image manip (config)
script.outputs['out_cfg'].link(manip.inputConfig)
# script -> image manip (frame)
script.outputs['out_frame'].link(manip.inputImage)

# image manip -> NN
manip.out.link(nn_yolo.input)

# NN -> out (host)
nn_yolo.out.link(xout_nn.input)  # detections


# ------------------
#  RUN THE PIPELINE
# ------------------
with depthai.Device(pipeline) as device:
    # host-side output queues to access the produced results
    # maxSize = 15, or choose any high number
    # blocking = False, to ensure the pipeline won't get stuck even if host does
    #   - pipeline will keep sending messages, and they will get overwritten in this queue
    videoQueue = device.getOutputQueue("video", maxSize=15, blocking=False)
    nnQueue = device.getOutputQueue("nn", maxSize=15, blocking=False)

    
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
    color_white = (255, 255, 255)
    # color_green = (0, 255, 0)
    # color_blue = (255, 0, 0)

    frame = None
    detections = []
    startTime = time.monotonic()
    counter = 0

    while True:
        # process input from camera (if any)
        if videoQueue.has() and nnQueue.has():      # sync video and NN
            frame = videoQueue.get().getCvFrame()

            bboxes = []
            confidences = []

            # if any QR codes were detected, display the image and highlight the codes with rectangles.
            # If not, just display the image.

            # process results from all cropped images
            for i in range(NUMBER_OF_CROPPED_IMAGES):

                # get the corresponding detections
                detections = nnQueue.get().detections
                counter += 1    # FPS will be per cropped frame
            
                # calculate coordinates of each detection wrt the original frame
                for detection in detections:
                    # transform the bounding box from the detections space <0..1> to the yolo frame space
                    bbox_detection = (detection.xmin, detection.ymin, detection.xmax, detection.ymax)
                    bbox_yolo_frame = transform_coords(np.array([1,1]), np.array([NN_INPUT_SIZE_W,NN_INPUT_SIZE_H]), bbox_detection)

                    # transform the bounding box from the yolo frame space to the coordinates in the original image
                    bbox = transform_coords(np.array([NN_INPUT_SIZE_W,NN_INPUT_SIZE_H]), wh_from_frame(frame, CROP_FACTOR), bbox_yolo_frame, wh_from_frame(frame, crop_vals[i]))
                    
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
                cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color_red, 2)
                cv2.putText(frame, f"{int(confidences[index] * 100)}%", (bbox[0] + 10, bbox[1] + 40), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color_red)

                print(f"QR code detected: coordinates: {bbox}, confidence: {confidences[index] * 100:.2f}%")            

            # display the original frame
            cv2.putText(frame, "NN fps: {:.2f}".format(counter / (time.monotonic() - startTime)), (2, frame.shape[0] - 4), cv2.FONT_HERSHEY_TRIPLEX, 0.4, color_white)
            cv2.imshow("Video", frame)

        # keyboard controls
        key = cv2.waitKey(1)
        # terminate the program when "q" is pressed
        if key == ord("q"):
            break
