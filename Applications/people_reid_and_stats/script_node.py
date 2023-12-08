import time

fps = 10  # default value
counter = 1
${FPS}
IMAGE_WIDTH = 1920
IMAGE_HEIGHT = 1080

while True:
    time.sleep(0.001)
    rgb_frame = node.io["rgb_frames"].tryGet()
    if rgb_frame is not None:
        counter += 1
        if counter == fps // 2:
            counter = 1
            # send to face detection model
            node.io["manip_face_img"].send(rgb_frame)

            # wait for face detection results
            face_detections = node.io["face_detections"].get()
            for face_detection in face_detections.detections:
                # send to emotion detection model - 64x64

                new_xmin = face_detection.xmin
                new_ymin = face_detection.ymin
                new_xmax = face_detection.xmax
                new_ymax = face_detection.ymax
                cfg = ImageManipConfig()
                # node.error(f"{(new_xmin, new_ymin, new_xmax, new_ymax)=}")
                cfg.setCropRect(new_xmin, new_ymin, new_xmax, new_ymax)
                cfg.setResize(64, 64)  # input size of: face-detection-retail-0004_openvino_2022.1_6shave.blob
                cfg.setKeepAspectRatio(False)
                node.io['manip_emotions_cfg'].send(cfg)
                node.io['manip_emotions_img'].send(rgb_frame)

                # send to age_gender model - 62x62
                cfg = ImageManipConfig()
                cfg.setCropRect(new_xmin, new_ymin, new_xmax, new_ymax)
                cfg.setResize(62, 62)  # input size of: age-gender-recognition-retail-0013_openvino_2022.1_6shave.blob
                cfg.setKeepAspectRatio(False)
                node.io['manip_age_gender_cfg'].send(cfg)
                node.io['manip_age_gender_img'].send(rgb_frame)
