
import time

fps = 10  # default value
counter = 1
${FPS}


while True:
    time.sleep(0.001)

    tracker = node.io["people_tracker"].get()
    rgb_frame = node.io["rgb_frames"].get()
    for t in tracker.tracklets:
        if t.status == Tracklet.TrackingStatus.NEW:
            det = t.srcImgDetection
            # send to re-id model - 128x256
            cfg = ImageManipConfig()
            cfg.setCropRect(det.xmin, det.ymin, det.xmax, det.ymax)
            cfg.setResize(128, 256)  # input size of: age-gender-recognition-retail-0013_openvino_2022.1_6shave.blob
            cfg.setKeepAspectRatio(False)
            node.error(f"sending into re_id")
            node.io['manip_reid_cfg'].send(cfg)
            node.io['manip_reid_img'].send(rgb_frame)
