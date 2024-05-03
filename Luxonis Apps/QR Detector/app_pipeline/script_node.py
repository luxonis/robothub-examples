
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

WIDTH_RELATIVE_SCALE = 2000 / 5312
HEIGHT_RELATIVE_SCALE = 2000 / 6000


def clamp(num, minimum, maximum):
    return max(minimum, min(num, maximum))


def run():
    while True:
        rgb_frame = node.io["rgb_frame"].get()
        for i in range(NUMBER_OF_CROPPED_IMAGES):
            xmin, ymin, = crop_vals[i]
            xmax, ymax = xmin + STEP_WIDTH + OVERLAP_WIDTH, ymin + STEP_HEIGHT + OVERLAP_HEIGHT
            cfg = ImageManipConfig()
            cfg.setCropRect(xmin, ymin, xmax, ymax)
            node.debug(f"Script {xmin:.2f}, {ymin:.2f}, {xmax:.2f}, {ymax:.2f}: ABS: {xmin*5312:.2f}, {ymin * 6000:.2f}, {xmax * 5312:.2f},"
                       f" {ymax * 6000:.2f} Width: {(xmax - xmin) * 5312}, Height: {(ymax - ymin) * 6000}")
            cfg.setResize(600, 600)
            cfg.setFrameType(ImgFrame.Type.BGR888p)
            cfg.setKeepAspectRatio(False)
            node.debug(f"Script QR Crop {i}")
            node.io['image_manip_1to1_crop_cfg'].send(cfg)
            node.io['image_manip_1to1_crop'].send(rgb_frame)


if __name__ == 'lpb':
    node.error(f"Script node starts as {__name__!r}.")
    run()
    node.error("Script node terminated.")
