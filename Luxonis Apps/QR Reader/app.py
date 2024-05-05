import logging as log

import depthai as dai
import robothub as rh

from app_pipeline import host_node, messages, oak_pipeline
from app_pipeline import script_node


### cv2 and av bug workaround on some linux systems - uncomment in local dev

# import cv2
# import numpy as np
#
# cv2.imshow("bugfix", np.zeros((10, 10, 3), dtype=np.uint8))
# cv2.destroyWindow("bugfix")

RESOLUTION_MAPPING = {
    "720p": (1280, 720),
    "1080p": (1920, 1080),
    "4k": (3840, 2160),
    "4000x3000": (4000, 3000),
    "5312x6000": (5312, 6000),
    "48MP": (5312, 6000)
}


class Application(rh.BaseDepthAIApplication):

    rgb_control = None

    def __init__(self):
        super().__init__()
        rh.CONFIGURATION["high_res_frame_width"] = RESOLUTION_MAPPING[rh.CONFIGURATION["resolution"]][0]
        rh.CONFIGURATION["high_res_frame_height"] = RESOLUTION_MAPPING[rh.CONFIGURATION["resolution"]][1]
        rh.CONFIGURATION["crop_count"] = script_node.NUMBER_OF_CROPPED_IMAGES
        rh.CONFIGURATION["high_res_crop_width"] = 600 if rh.CONFIGURATION["resolution"] == "5312x6000" else 768
        rh.CONFIGURATION["high_res_crop_height"] = 600 if rh.CONFIGURATION["resolution"] == "5312x6000" else 432
        rh.CONFIGURATION["merged_image_overlap"] = 0.25 if rh.CONFIGURATION["resolution"] == "5312x6000" else 0.25
        rh.CONFIGURATION["merged_image_width"] = 1500 if rh.CONFIGURATION["resolution"] == "5312x6000" else 1920
        rh.CONFIGURATION["merged_image_height"] = 1500 if rh.CONFIGURATION["resolution"] == "5312x6000" else 1080

    def setup_pipeline(self) -> dai.Pipeline:
        log.info(f"Configuration: {rh.CONFIGURATION}")
        pipeline = dai.Pipeline()
        oak_pipeline.create_pipeline(pipeline=pipeline)
        return pipeline

    def manage_device(self, device: dai.Device):
        log.info(f"DepthAi version: {dai.__version__}")

        self.rgb_control = device.getInputQueue(name="rgb_input")
        script_node_input = device.getInputQueue(name="script_node_input")
        script_node_qr_crops_input = device.getInputQueue(name="script_node_qr_crops_input")
        self._send_resolution_config_to_script_node(script_node_input)
        self._send_resolution_config_to_script_node(script_node_qr_crops_input)

        high_res_frames = host_node.Bridge(device=device, out_name="high_res_frames", blocking=False, queue_size=3)
        qr_crops_queue = device.getOutputQueue(name="qr_crops", maxSize=10, blocking=True)
        qr_detection_out = host_node.Bridge(device=device, out_name="qr_detection_out", blocking=False, queue_size=9)

        qr_bboxes = host_node.ReconstructQrDetections(input_node=qr_detection_out)
        high_res_frames = host_node.HighResFramesGatherer(input_node=high_res_frames)
        qr_boxes_and_frame_sync = host_node.Sync(inputs=[high_res_frames, qr_bboxes],
                                                 input_names=["high_res_rgb", "qr_bboxes"],
                                                 output_message_obj=messages.FramesWithDetections)
        qr_code_decoder = host_node.QrCodeDecoder(input_node=qr_boxes_and_frame_sync, qr_crop_queue=qr_crops_queue)
        host_node.ResultsReporter(input_node=qr_code_decoder)
        host_node.Monitor(input_node=qr_code_decoder, name="qr_boxes_and_frame_sync")

        log.info(f"Application started")
        host_node.Bridge.run(device_stop_event=self._device_stop_event)

    def _send_resolution_config_to_script_node(self, input_queue: dai.DataInputQueue):
        message = dai.Buffer()
        data = [0] if rh.CONFIGURATION["resolution"] == "5312x6000" else [1]
        message.setData(data)
        input_queue.send(message)

    def on_configuration_changed(self, configuration_changes: dict) -> None:
        log.info(f"CONFIGURATION CHANGES: {configuration_changes}")
        require_restart = ["fps", "auto_exposure_limit"]
        for key in require_restart:
            if key in configuration_changes:
                log.info(f"{key} change needs a new pipeline. Restarting OAK device...")
                self.restart_device()
        if (("manual_exposure" in configuration_changes or "manual_iso" in configuration_changes or
             "enable_manual_exposure" in configuration_changes) and rh.CONFIGURATION["enable_manual_exposure"]):
            log.info(f"Setting manual exposure to {rh.CONFIGURATION['manual_exposure']} and iso to {rh.CONFIGURATION['manual_iso']}")
            ctrl = dai.CameraControl()
            ctrl.setManualExposure(rh.CONFIGURATION["manual_exposure"], rh.CONFIGURATION["manual_iso"])
            self.rgb_control.send(ctrl)
        if "enable_manual_exposure" in configuration_changes and not rh.CONFIGURATION["enable_manual_exposure"]:
            ctrl = dai.CameraControl()
            ctrl.setAutoExposureEnable()
            self.rgb_control.send(ctrl)
        if "manual_focus" in configuration_changes and rh.CONFIGURATION["manual_focus"] > 0:
            log.info(f"Setting manual focus to {rh.CONFIGURATION['manual_focus']}")
            ctrl = dai.CameraControl()
            ctrl.setManualFocus(rh.CONFIGURATION["manual_focus"])
            self.rgb_control.send(ctrl)


if __name__ == "__main__":
    app = Application()
    app.run()
