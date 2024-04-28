
NUMBER_OF_CROPPED_IMAGES = 9
crop_vals = [(0.0, 0.0), (0.0, 0.3), (0.0, 0.6), (0.3, 0.0), (0.3, 0.3), (0.3, 0.6), (0.6, 0.0), (0.6, 0.3), (0.6, 0.6)]
STEP = 0.4

while True:
    rgb_frame = node.io["rgb_frame"].get()
    for i in range(NUMBER_OF_CROPPED_IMAGES):
        xmin, ymin, = crop_vals[i]
        xmax, ymax = xmin + STEP, ymin + STEP
        cfg = ImageManipConfig()
        cfg.setCropRect(xmin, ymin, xmax, ymax)
        cfg.setKeepAspectRatio(False)

        node.io['image_manip_nn_crop_cfg'].send(cfg)
        node.io['image_manip_nn_crop'].send(rgb_frame)