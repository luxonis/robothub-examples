import cv2
import depthai as dai
import image_drawing as img

from people_tracking import PeopleTracking
from people_tracking_sync import PeopleTrackingSync
from depthai_sdk import OakCamera, FramePacket
from face_features import FaceFeatures
from monitor import Monitor
from people_faces_sync import PeopleFacesSync
from pipeline_robothub import create_pipeline as get_pipeline_depthai

CONFIGURATION = {"fps": 8}
FOCUS = 150
INCREMENT = 5


def run_reid_app():
    global FOCUS, INCREMENT
    with OakCamera() as oak:
        get_pipeline_depthai(oak, CONFIGURATION)
        oak.start(blocking=False)

        rgb_input = oak.device.getInputQueue(name="rgb_input")
        rgb_preview = oak.device.getOutputQueue(name="rgb_preview", maxSize=5, blocking=False)
        object_detections = oak.device.getOutputQueue(name="object_detection_nn", maxSize=5, blocking=False)
        face_detections = oak.device.getOutputQueue(name="face_detection_nn", maxSize=5, blocking=False)
        emotion_detections = oak.device.getOutputQueue(name="emotion_detection_nn", maxSize=20, blocking=False)
        age_gender_detections = oak.device.getOutputQueue(name="age_gender_detection_nn", maxSize=20, blocking=False)
        # re_id = oak.device.getOutputQueue(name="re_id_nn", maxSize=20, blocking=False)
        re_id = None
        tracker = oak.device.getOutputQueue(name="object_tracker", maxSize=5, blocking=False)

        # host nodes
        face_features = FaceFeatures(age_gender_queue=age_gender_detections, emotions_queue=emotion_detections)
        people_tracking_sync = PeopleTrackingSync()
        people_tracking = PeopleTracking(input_node=people_tracking_sync, re_id_queue=re_id)
        people_faces_sync = PeopleFacesSync(people_tracking=people_tracking, face_features=face_features)
        # monitor = Monitor(input_node=people_faces_sync)
        rgb_frame: dai.ImgFrame = None
        tracker_frame: dai.Tracklets = None
        face_detections_frame: dai.ImgDetections = None

        while True:
            if cv2.waitKey(10) == ord("q"):
                print(f"terminating")
                break
            if cv2.waitKey(10) == ord("f"):
                print(f"decreasing focus value")
                FOCUS -= INCREMENT
                set_focus(value=FOCUS, input_queue=rgb_input)
            if cv2.waitKey(10) == ord("r"):
                print(f"increasing focus value")
                FOCUS += INCREMENT
                set_focus(value=FOCUS, input_queue=rgb_input)
            if rgb_preview.has():
                rgb_frame: dai.ImgFrame = rgb_preview.get()
                people_tracking_sync.rgb_frame_callback(rgb_frame=rgb_frame)
            if object_detections.has():
                object_detections_frame: dai.ImgDetections = object_detections.get()
                people_tracking_sync.people_detections_callback(people_detections_frame=object_detections_frame)
            if tracker.has():
                tracker_frame = tracker.get()
                people_tracking_sync.object_tracker_callback(object_tracker_frame=tracker_frame)
            if face_detections.has():
                face_detections_frame: dai.ImgDetections = face_detections.get()
                face_features.face_features_callback(face_detections_frame=face_detections_frame)
                print(f"Faces ID: {face_detections_frame.getSequenceNum()}")

            # visualize(rgb_frame=rgb_frame, tracker_frame=tracker_frame, face_detections_frame=face_detections_frame)


def set_focus(value, input_queue):
    print(f"Set focus with {value=}")
    if value < 0:
        value = 10
    elif value > 255:
        value = 255
    ctrl = dai.CameraControl()
    ctrl.setManualFocus(value)
    input_queue.send(ctrl)

def visualize(rgb_frame: dai.ImgFrame, tracker_frame: dai.Tracklets, face_detections_frame: dai.ImgDetections) -> None:
    if rgb_frame is None:
        return
    frame = rgb_frame.getCvFrame()
    # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    if tracker_frame is not None:
        for tracklet in tracker_frame.tracklets:
            bbox = tracklet.srcImgDetection
            img.draw_text(image=frame, text=f"{tracklet.id}", bottom_left_position=(int(bbox.xmin * 1920), int(bbox.ymax * 1080)))
            img.draw_rectangle(image=frame, bottom_left=(int(bbox.xmin * 1920), int(bbox.ymax * 1080)),
                               top_right=(int(bbox.xmax * 1920), int(bbox.ymin * 1080)))
    if face_detections_frame is not None:
        for face in face_detections_frame.detections:
            img.draw_rectangle(image=frame, bottom_left=(int(face.xmin * 1920), int(face.ymax * 1080)),
                               top_right=(int(face.xmax * 1920), int(face.ymin * 1080)), color=(255, 0, 255))
    cv2.imshow("frame", frame)


if __name__ == "__main__":
    run_reid_app()
