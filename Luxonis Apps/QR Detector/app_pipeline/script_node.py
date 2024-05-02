
NUMBER_OF_CROPPED_IMAGES = 9
STEP = 0.3
OVERLAP = 0.1
crop_vals = [(0.0, 0.0), (0.0, STEP), (0.0, STEP * 2), (STEP, 0.0), (STEP, STEP), (STEP, STEP * 2), (STEP * 2, 0.0), (STEP * 2, STEP),
             (STEP * 2, STEP * 2)]

PADDING = 0.01


def clamp(num, minimum, maximum):
    return max(minimum, min(num, maximum))


def run():
    while True:
        node.error(f"Script Calling get() on high res frame")
        rgb_frame = node.io["rgb_frame"].get()
        seq_num = rgb_frame.getSequenceNum()
        for i in range(NUMBER_OF_CROPPED_IMAGES):
            xmin, ymin, = crop_vals[i]
            xmax, ymax = xmin + STEP + OVERLAP, ymin + STEP + OVERLAP
            cfg = ImageManipConfig()
            cfg.setCropRect(xmin, ymin, xmax, ymax)
            cfg.setResize(1000, 1000)
            cfg.setFrameType(ImgFrame.Type.BGR888p)
            cfg.setKeepAspectRatio(False)
            node.error(f"Script QR Crop {i}")
            node.io['image_manip_1to1_crop_cfg'].send(cfg)
            node.io['image_manip_1to1_crop'].send(rgb_frame)

        counter = 0
        for i in range(NUMBER_OF_CROPPED_IMAGES):
            node.error(f"Script Calling get() on nn detections {i}")
            qr_detections = node.io["qr_detection_nn"].get()
            for detection in qr_detections.detections:
                node.error(f"Script QR Detection {counter}")
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


if __name__ == 'lpb':
    node.error(f"Script node starts as {__name__!r}.")
    run()
    node.error("Script node terminated.")
