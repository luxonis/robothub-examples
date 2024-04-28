import logging as log

import depthai as dai
import robothub as rh

from app_pipeline import host_node, messages, oak_pipeline

### cv2 and av bug workaround on some linux systems - uncomment in local dev

# import cv2
# import numpy as np
#
# cv2.imshow("bugfix", np.zeros((10, 10, 3), dtype=np.uint8))
# cv2.destroyWindow("bugfix")


class Application(rh.BaseDepthAIApplication):

    rgb_control = None

    def __init__(self):
        super().__init__()
        rh.CONFIGURATION["h264_frame_width"] = 1280
        rh.CONFIGURATION["h264_frame_height"] = 720

    def setup_pipeline(self) -> dai.Pipeline:
        pipeline = dai.Pipeline()
        oak_pipeline.create_pipeline(pipeline=pipeline)
        return pipeline

    def manage_device(self, device: dai.Device):
        log.info(f"DepthAi version: {dai.__version__}")

        self.rgb_control = device.getInputQueue(name="rgb_input")
        video_h264_encoded = host_node.Bridge(device=device, out_name="video_h264_encoded", blocking=False, queue_size=3)
        rgb_video_high_res = host_node.Bridge(device=device, out_name="rgb_isp_high_res", blocking=False, queue_size=2)
        qr_detection_out = host_node.Bridge(device=device, out_name="qr_detection_out", blocking=False, queue_size=3)

        qr_bboxes = host_node.ReconstructQrDetections(input_node=qr_detection_out)
        qr_boxes_and_frame_sync = host_node.Sync(inputs=[video_h264_encoded, rgb_video_high_res, qr_bboxes],
                                                 input_names=["rgb_h264", "rgb_video_high_res", "qr_bboxes"],
                                                 output_message_obj=messages.FramesWithDetections)
        qr_code_decoder = host_node.QrCodeDecoder(input_node=qr_boxes_and_frame_sync)
        video_reporter = host_node.VideoReporter(input_node=video_h264_encoded)
        host_node.ResultsReporter(input_node=qr_code_decoder, video_reporter_trigger=video_reporter.trigger_video_report)
        host_node.Monitor(input_node=qr_code_decoder, name="qr_boxes_and_frame_sync")

        log.info(f"Application started")
        host_node.Bridge.run(device_stop_event=self._device_stop_event)

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
