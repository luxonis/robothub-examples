
NUMBER_OF_CROPPED_IMAGES = 9
crop_vals = [(0.0, 0.0), (0.0, 0.3), (0.0, 0.6), (0.3, 0.0), (0.3, 0.3), (0.3, 0.6), (0.6, 0.0), (0.6, 0.3), (0.6, 0.6)]
STEP = 0.4
PADDING = 0.01


def clamp(num, minimum, maximum):
    return max(minimum, min(num, maximum))


while True:
    rgb_frame = node.io["rgb_frame"].get()
    seq_num = rgb_frame.getSequenceNum()
    for i in range(NUMBER_OF_CROPPED_IMAGES):
        xmin, ymin, = crop_vals[i]
        xmax, ymax = xmin + STEP, ymin + STEP
        cfg = ImageManipConfig()
        cfg.setCropRect(xmin, ymin, xmax, ymax)
        cfg.setResize(1000, 1000)
        cfg.setFrameType(ImgFrame.Type.BGR888p)
        cfg.setKeepAspectRatio(False)

        node.io['image_manip_1to1_crop_cfg'].send(cfg)
        node.io['image_manip_1to1_crop'].send(rgb_frame)

    counter = 0
    for i in range(NUMBER_OF_CROPPED_IMAGES):
        qr_detections = node.io["qr_detection_nn"].get()
        for detection in qr_detections.detections:
            node.error(f"Script QR Crop {counter}")
            counter += 1
            xmin, ymin, xmax, ymax = detection.xmin - PADDING, detection.ymin - PADDING, detection.xmax + PADDING, detection.ymax + PADDING
            xmin = clamp(xmin, 0, 0.93)
            ymin = clamp(ymin, 0, 0.93)
            xmax = clamp(xmax, xmin + 0.01, 1)
            ymax = clamp(ymax, ymin + 0.01, 1)
            cfg = ImageManipConfig()
            cfg.setCropRect(xmin, ymin, xmax, ymax)
            cfg.setKeepAspectRatio(False)
            cfg.setFrameType(ImgFrame.Type.BGR888p)

            node.io['to_qr_crop_manip_cfg'].send(cfg)
            node.io['to_qr_crop_manip'].send(high_res_frame)
