import robothub as rh
import zxingcpp

from app_pipeline import host_node, messages

__all__ = ["QrCodeDecoder"]


class QrCodeDecoder(host_node.BaseNode):
    """Add cr code text to qr bounding boxes."""
    DECODE_CHANNEL = 0  # blue channel should be enough for QR decoding
    PADDING = 20

    def __init__(self, input_node: host_node.BaseNode):
        super().__init__()
        input_node.set_callback(callback=self.__callback)

    @rh.decorators.measure_average_performance(report_every_minutes=1)
    def __callback(self, frames_and_detections: messages.FramesWithDetections):
        qr_bboxes = frames_and_detections.qr_bboxes
        high_res_frame = frames_and_detections.rgb_video_high_res.getCvFrame()
        for bbox in qr_bboxes.bounding_boxes:
            xmin, ymin, xmax, ymax = bbox.transform(width=1920 * 2, height=1080 * 2)
            # cv2.rectangle(high_res_frame, (int(xmin), int(ymin)), (int(xmax), int(ymax)), (0, 0, 255), 2)
            qr_code_crop = high_res_frame[ymin - self.PADDING:ymax + self.PADDING, xmin - self.PADDING:xmax + self.PADDING, self.DECODE_CHANNEL]
            decoded_codes = zxingcpp.read_barcodes(qr_code_crop)
            if len(decoded_codes) > 0:
                decoded_code = decoded_codes[0]
                bbox.set_label(label=decoded_code.text)
        # cv2.imshow("4k", high_res_frame)
        self.send_message(frames_and_detections)
