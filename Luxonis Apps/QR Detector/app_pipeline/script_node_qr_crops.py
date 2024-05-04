

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

PADDING = 0.001

WIDTH_RELATIVE_SCALE = 2000 / 5312
HEIGHT_RELATIVE_SCALE = 2000 / 6000


def clamp(num, minimum, maximum):
    return max(minimum, min(num, maximum))


def run():
    message = node.io["script_node_qr_crops_input"].get()
    data = message.getData()
    node.error(f"Data received: {data[0]}")
    resolution = data[0]  # 0 for 5312x6000, 1 for 4k
    while True:
        rgb_frame = node.io["rgb_frame"].get()
        counter = 0
        for i in range(NUMBER_OF_CROPPED_IMAGES):
            node.debug(f"Script Calling get() on nn detections {i}")
            qr_detections = node.io["qr_detection_nn"].get()
            xmin_orig_frame, ymin_orig_frame, = crop_vals[i]
            for detection in qr_detections.detections:
                node.debug(f"Script QR Detection {counter}")
                counter += 1
                xmin, ymin, xmax, ymax = (detection.xmin * WIDTH_RELATIVE_SCALE + xmin_orig_frame - PADDING,
                                          detection.ymin * HEIGHT_RELATIVE_SCALE + ymin_orig_frame - PADDING,
                                          detection.xmax * WIDTH_RELATIVE_SCALE + xmin_orig_frame + PADDING,
                                          detection.ymax * HEIGHT_RELATIVE_SCALE + ymin_orig_frame + PADDING)
                node.debug(f"QR CROP {i}: {xmin:.2f}, {ymin:.2f}, {xmax:.2f}, {ymax:.2f}")
                node.debug(f"{detection.xmin:.2f}, {detection.ymin:.2f}, {detection.xmax:.2f}, {detection.ymax:.2f}, {xmin_orig_frame}, {ymin_orig_frame}, {WIDTH_RELATIVE_SCALE}, {HEIGHT_RELATIVE_SCALE}")
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
