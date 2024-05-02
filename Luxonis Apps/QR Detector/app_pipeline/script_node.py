
NUMBER_OF_CROPPED_IMAGES = 9
STEP = 0.3
OVERLAP = 0.1
WIDTH_OFFSET = (156 / 5312)
HEIGHT_OFFSET = (500 / 6000)
WIDTH_RANGE = (5156 / 5312) - WIDTH_OFFSET
HEIGHT_RANGE = (5500 / 6000) - HEIGHT_OFFSET
STEP_HEIGHT = HEIGHT_RANGE * STEP
STEP_WIDTH = WIDTH_RANGE * STEP
OVERLAP_HEIGHT = HEIGHT_RANGE * OVERLAP
OVERLAP_WIDTH = WIDTH_RANGE * OVERLAP

# original frame is 5312x6000 and we want to crop 9 images from 5000x5000 crop
crop_vals = [(WIDTH_OFFSET, HEIGHT_OFFSET), (WIDTH_OFFSET, STEP_HEIGHT + HEIGHT_OFFSET), (WIDTH_OFFSET, STEP_HEIGHT * 2 + HEIGHT_OFFSET),
             (STEP_WIDTH + WIDTH_OFFSET, HEIGHT_OFFSET), (STEP_WIDTH + WIDTH_OFFSET, STEP_HEIGHT + HEIGHT_OFFSET), (STEP_WIDTH + WIDTH_OFFSET, STEP_HEIGHT * 2 + HEIGHT_OFFSET),
             (STEP_WIDTH * 2 + WIDTH_OFFSET, HEIGHT_OFFSET), (STEP_WIDTH * 2 + WIDTH_OFFSET, STEP_HEIGHT + HEIGHT_OFFSET), (STEP_WIDTH * 2 + WIDTH_OFFSET, STEP_HEIGHT * 2 + HEIGHT_OFFSET)]

PADDING = 0.01


def clamp(num, minimum, maximum):
    return max(minimum, min(num, maximum))


def run():
    while True:
        node.debug(f"Script Calling get() on high res frame")
        rgb_frame = node.io["rgb_frame"].get()
        seq_num = rgb_frame.getSequenceNum()
        for i in range(NUMBER_OF_CROPPED_IMAGES):
            xmin, ymin, = crop_vals[i]
            xmax, ymax = xmin + STEP_WIDTH + OVERLAP_WIDTH, ymin + STEP_HEIGHT + OVERLAP_HEIGHT
            cfg = ImageManipConfig()
            cfg.setCropRect(xmin, ymin, xmax, ymax)
            node.error(f"Script {xmin}, {ymin}, {xmax}, {ymax}")
            cfg.setResize(1000, 1000)
            cfg.setFrameType(ImgFrame.Type.BGR888p)
            cfg.setKeepAspectRatio(False)
            node.debug(f"Script QR Crop {i}")
            node.io['image_manip_1to1_crop_cfg'].send(cfg)
            node.io['image_manip_1to1_crop'].send(rgb_frame)

        counter = 0
        for i in range(NUMBER_OF_CROPPED_IMAGES):
            node.debug(f"Script Calling get() on nn detections {i}")
            qr_detections = node.io["qr_detection_nn"].get()
            for detection in qr_detections.detections:
                node.debug(f"Script QR Detection {counter}")
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
                node.io['to_qr_crop_manip'].send(rgb_frame)


if __name__ == 'lpb':
    node.error(f"Script node starts as {__name__!r}.")
    run()
    node.error("Script node terminated.")
