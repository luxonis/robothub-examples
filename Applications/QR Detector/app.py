import cv2
import depthai
import numpy as np
import time
import zxingcpp

from datetime import datetime
from pathlib import Path


NN_INPUT_SIZE_W = 512
NN_INPUT_SIZE_H = 288

CONFIDENCE_THRESHOLD = 0.2

NUMBER_OF_CROPPED_IMAGES = 9
crop_vals = [(0.0, 0.0), (0.0, 0.3), (0.0, 0.6), (0.3, 0.0), (0.3, 0.3), (0.3, 0.6), (0.6, 0.0), (0.6, 0.3), (0.6, 0.6)]


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
cam.setColorOrder(depthai.ColorCameraProperties.ColorOrder.BGR)
cam.setInterleaved(False)
cam.setPreviewSize(1920,1080)

# Script
# https://docs.luxonis.com/projects/api/en/latest/components/nodes/script/
script = pipeline.create(depthai.node.Script)
# wait for the output of the corresponding image manip and send it to the NN,
# making sure the frames are passed in the right order
script.setScript("""
    import time
    
    NUMBER_OF_CROPPED_IMAGES = 9

    while True:
        start = time.perf_counter()
        for i in range(NUMBER_OF_CROPPED_IMAGES):
            input_name = f"in_im{i}"
            frame = node.io[input_name].get()
            node.io['out_frame'].send(frame)
        elapsed = time.perf_counter() - start
        node.warn(f"Time elapsed: {elapsed:.5f} s")
""")


# ImageManip nodes with corresponding configs
# https://docs.luxonis.com/projects/api/en/latest/components/nodes/image_manip/
def create_image_manip(crop):
    # create the node
    manip = pipeline.create(depthai.node.ImageManip)
    
    # default config values
    manip.initialConfig.setFrameType(depthai.ImgFrame.Type.BGR888p)
    manip.initialConfig.setResize(NN_INPUT_SIZE_W, NN_INPUT_SIZE_H)
    step = 0.4
    xmin = crop[0]
    ymin = crop[1]
    xmax = xmin + step
    ymax = ymin + step
    manip.initialConfig.setCropRect(xmin, ymin, xmax, ymax)
    
    # input image settings
    manip.inputImage.setWaitForMessage(True)
    manip.inputImage.setBlocking(True)
    manip.inputImage.setQueueSize(1)
    manip.setMaxOutputFrameSize(NN_INPUT_SIZE_W * NN_INPUT_SIZE_H * 3)

    return manip

# connect the camera preview to each image manip's input,
# connect each image manip's output to the Script node's input
for i in range(NUMBER_OF_CROPPED_IMAGES):
    im = create_image_manip(crop_vals[i])
    
    # camera (preview) > image manip
    cam.preview.link(im.inputImage)

    # image manip > script
    input_name = f"in_im{i}"
    im.out.link(script.inputs[input_name])

    # script input settings
    script.inputs[input_name].setBlocking(True)
    script.inputs[input_name].setQueueSize(1)


# YoloDetectionNetwork
# https://docs.luxonis.com/projects/api/en/latest/components/nodes/yolo_detection_network/
nn_yolo = pipeline.create(depthai.node.YoloDetectionNetwork)
nn_yolo.setBlobPath(str((Path(__file__).parent / Path('qr_model_512x288_rvc2_openvino_2022.1_6shave.blob')).resolve().absolute()))
nn_yolo.setConfidenceThreshold(CONFIDENCE_THRESHOLD)
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
# camera (preview) -> host
cam.preview.link(xout_video.input)

# script -> NN
script.outputs['out_frame'].link(nn_yolo.input)

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
  
    CROP_FACTOR = 0.4   # corresponds to "step" in the Script node

    
    # scale_factor can be scalar (= same for both x,y) or vector [scale_x, scale_y]
    def wh_from_frame(frame, scale_factor = 1):
        # CONSIDER: is this flipping a good idea? it seems confusing when indexing frames (CV images)
        # which use "matrix" indexing - i,j (height, width)
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

        res = bbox * S + M

        # clip the result to get rid of negative numbers that might occur
        np.clip(res, a_min=0, a_max=None, out=res)  # in-place clipping

        return res.astype(int)


    
    color_red = (0, 0, 255)
    color_white = (255, 255, 255)
    # color_green = (0, 255, 0)
    # color_blue = (255, 0, 0)

    # a border to keep around each detected code - decoding is hard(er) to impossible without a border.
    # 10 px seems to work well
    BORDER_SIZE = 10

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

            # If any codes were detected, display the image, highlight the codes with rectangles,
            # display the decoded text (if available) above the highlighting rectangle,
            # and print the relevant info to the output.
            # Note: the highlighted rectangles include an (additional) border necessary for code decoding.
            # If no codes were detected, just display the image.

            # process results from all cropped images
            for i in range(NUMBER_OF_CROPPED_IMAGES):

                # get the corresponding detections
                detections = nnQueue.get().detections
                counter += 1    # FPS will be counted per cropped frame
            
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
            confidence_threshold = CONFIDENCE_THRESHOLD     # generally should match yolo's confidence_threshold
            overlap_threshold = 0.01
            nmsboxes = [(bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1]) for bbox in bboxes]
            indices = cv2.dnn.NMSBoxes(nmsboxes, confidences, confidence_threshold, overlap_threshold)
            
            # display and print info about each resulting code and try to decode it. 
            # If successful, display and print the decoded text as well.
            for index in indices:
                bbox = bboxes[index]
                # cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color_red, 2)
                # cv2.putText(frame, f"{int(confidences[index] * 100)}%", (bbox[0] + 10, bbox[1] + 40), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color_red)

                timestamp = datetime.now().strftime("%T.%f")

                print(f"{timestamp} Code detected: coordinates: {bbox}, confidence: {confidences[index] * 100:.2f}%")
                
                # QR decoding
                
                # make sure the selection dims won't exceed the frame dims
                x_from = max((bbox[0] - BORDER_SIZE), 0)
                x_to = min((bbox[2] + BORDER_SIZE), np.shape(frame)[1])
                y_from = max((bbox[1] - BORDER_SIZE), 0)
                y_to = min((bbox[3] + BORDER_SIZE), np.shape(frame)[0])
                channel = 0     # blue channel is enough

                # highlight the detected code in the video frame
                cv2.rectangle(frame, (x_from, y_from), (x_to, y_to), color_red, 2)

                # selection - detected code with a border
                detected_code = frame[y_from:y_to, x_from:x_to, channel]
                
                # try to decode it
                decoded_codes = zxingcpp.read_barcodes(detected_code)
                for code in decoded_codes:
                    timestamp = datetime.now().strftime("%T.%f")
                    print(f'{timestamp} Code decoded: "{code.text}"')
                    
                    cv2.putText(frame, f"{code.text}", (bbox[0] + 10, bbox[1] - 20), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color_red)


            # display the video frame
            cv2.putText(frame, "NN fps: {:.2f}".format(counter / (time.monotonic() - startTime)), (2, frame.shape[0] - 4), cv2.FONT_HERSHEY_TRIPLEX, 0.4, color_white)
            cv2.imshow("Video", frame)


        # keyboard controls
        key = cv2.waitKey(1)
        # terminate the program when "q" is pressed
        if key == ord("q"):
            break
