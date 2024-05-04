

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

    # original frame is 5312x6000 and we want to crop 9 images from 5000x5000 crop
    crop_vals = [(_WIDTH_OFFSET, _HEIGHT_OFFSET), (_WIDTH_OFFSET, STEP_HEIGHT + _HEIGHT_OFFSET), (_WIDTH_OFFSET, STEP_HEIGHT * 2 + _HEIGHT_OFFSET),
                 (STEP_WIDTH + _WIDTH_OFFSET, _HEIGHT_OFFSET), (STEP_WIDTH + _WIDTH_OFFSET, STEP_HEIGHT + _HEIGHT_OFFSET), (STEP_WIDTH + _WIDTH_OFFSET, STEP_HEIGHT * 2 + _HEIGHT_OFFSET),
                 (STEP_WIDTH * 2 + _WIDTH_OFFSET, _HEIGHT_OFFSET), (STEP_WIDTH * 2 + _WIDTH_OFFSET, STEP_HEIGHT + _HEIGHT_OFFSET), (STEP_WIDTH * 2 + _WIDTH_OFFSET, STEP_HEIGHT * 2 + _HEIGHT_OFFSET)]


class ImageProperties4k:
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

    # original frame is 5312x6000 and we want to crop 9 images from 5000x5000 crop
    crop_vals = [(_WIDTH_OFFSET, _HEIGHT_OFFSET), (_WIDTH_OFFSET, STEP_HEIGHT + _HEIGHT_OFFSET), (_WIDTH_OFFSET, STEP_HEIGHT * 2 + _HEIGHT_OFFSET),
                 (STEP_WIDTH + _WIDTH_OFFSET, _HEIGHT_OFFSET), (STEP_WIDTH + _WIDTH_OFFSET, STEP_HEIGHT + _HEIGHT_OFFSET),
                 (STEP_WIDTH + _WIDTH_OFFSET, STEP_HEIGHT * 2 + _HEIGHT_OFFSET),
                 (STEP_WIDTH * 2 + _WIDTH_OFFSET, _HEIGHT_OFFSET), (STEP_WIDTH * 2 + _WIDTH_OFFSET, STEP_HEIGHT + _HEIGHT_OFFSET),
                 (STEP_WIDTH * 2 + _WIDTH_OFFSET, STEP_HEIGHT * 2 + _HEIGHT_OFFSET)]


def clamp(num, minimum, maximum):
    return max(minimum, min(num, maximum))


def run():
    message = node.io["script_node_input"].get()
    data = message.getData()
    node.error(f"Data received: {data[0]}")
    resolution = data[0]  # 0 for 5312x6000, 1 for 4k
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
