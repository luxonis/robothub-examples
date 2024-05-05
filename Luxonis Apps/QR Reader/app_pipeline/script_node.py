

NUMBER_OF_CROPPED_IMAGES = 9

class ImageProperties5312x6000:
    _STEP = 0.3
    _OVERLAP = 0.1
    _WIDTH_OFFSET = (156 / 5312)
    _HEIGHT_OFFSET = (500 / 6000)
    _WIDTH_RANGE = (5156 / 5312) - _WIDTH_OFFSET
    _HEIGHT_RANGE = (5500 / 6000) - _HEIGHT_OFFSET
    STEP_HEIGHT = _HEIGHT_RANGE * _STEP
    STEP_WIDTH = _WIDTH_RANGE * _STEP
    OVERLAP_HEIGHT = _HEIGHT_RANGE * _OVERLAP
    OVERLAP_WIDTH = _WIDTH_RANGE * _OVERLAP
    RESIZE_WIDTH = 600
    RESIZE_HEIGHT = 600

    # original frame is 5312x6000 and we want to crop 9 images from 5000x5000 crop
    crop_vals = [(_WIDTH_OFFSET, _HEIGHT_OFFSET), (_WIDTH_OFFSET, STEP_HEIGHT + _HEIGHT_OFFSET), (_WIDTH_OFFSET, STEP_HEIGHT * 2 + _HEIGHT_OFFSET),
                 (STEP_WIDTH + _WIDTH_OFFSET, _HEIGHT_OFFSET), (STEP_WIDTH + _WIDTH_OFFSET, STEP_HEIGHT + _HEIGHT_OFFSET), (STEP_WIDTH + _WIDTH_OFFSET, STEP_HEIGHT * 2 + _HEIGHT_OFFSET),
                 (STEP_WIDTH * 2 + _WIDTH_OFFSET, _HEIGHT_OFFSET), (STEP_WIDTH * 2 + _WIDTH_OFFSET, STEP_HEIGHT + _HEIGHT_OFFSET), (STEP_WIDTH * 2 + _WIDTH_OFFSET, STEP_HEIGHT * 2 + _HEIGHT_OFFSET)]


class ImageProperties4k:
    crop_vals = [(0.0, 0.0), (0.0, 0.3), (0.0, 0.6), (0.3, 0.0), (0.3, 0.3), (0.3, 0.6), (0.6, 0.0), (0.6, 0.3), (0.6, 0.6)]
    STEP_HEIGHT = 0.3
    STEP_WIDTH = 0.3
    OVERLAP_HEIGHT = 0.1
    OVERLAP_WIDTH = 0.1
    RESIZE_WIDTH = 768
    RESIZE_HEIGHT = 432


IMG_PROPS = None


def clamp(num, minimum, maximum):
    return max(minimum, min(num, maximum))


def run():
    message = node.io["script_node_input"].get()
    data = message.getData()
    node.error(f"Data received: {data[0]}")
    resolution = data[0]  # 0 for 5312x6000, 1 for 4k
    if resolution == 0:
        IMG_PROPS = ImageProperties5312x6000()
    else:
        IMG_PROPS = ImageProperties4k()

    while True:
        rgb_frame = node.io["rgb_frame"].get()
        for i in range(NUMBER_OF_CROPPED_IMAGES):
            xmin, ymin, = IMG_PROPS.crop_vals[i]
            xmax, ymax = xmin + IMG_PROPS.STEP_WIDTH + IMG_PROPS.OVERLAP_WIDTH, ymin + IMG_PROPS.STEP_HEIGHT + IMG_PROPS.OVERLAP_HEIGHT
            cfg = ImageManipConfig()
            cfg.setCropRect(xmin, ymin, xmax, ymax)
            node.debug(f"Script {xmin:.2f}, {ymin:.2f}, {xmax:.2f}, {ymax:.2f}: ABS: {xmin*5312:.2f}, {ymin * 6000:.2f}, {xmax * 5312:.2f},"
                       f" {ymax * 6000:.2f} Width: {(xmax - xmin) * 5312}, Height: {(ymax - ymin) * 6000}")
            cfg.setResize(IMG_PROPS.RESIZE_WIDTH, IMG_PROPS.RESIZE_HEIGHT)
            cfg.setFrameType(ImgFrame.Type.BGR888p)
            cfg.setKeepAspectRatio(False)
            node.debug(f"Script QR Crop {i}")
            node.io['image_manip_1to1_crop_cfg'].send(cfg)
            node.io['image_manip_1to1_crop'].send(rgb_frame)


if __name__ == 'lpb':
    node.error(f"Script node starts as {__name__!r}.")
    run()
    node.error("Script node terminated.")
