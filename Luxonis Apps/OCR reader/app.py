import logging as log

import blobconverter
import depthai as dai
import east
import easyocr
import numpy as np
import robothub as rh


def create_output(pipeline: dai.Pipeline, input: dai.Node.Output, stream_name: str):
    xout = pipeline.createXLinkOut()
    xout.setStreamName(stream_name)
    input.link(xout.input)
    return xout


CAM_SIZE = (1024, 1024)
NN_SIZE = (256, 256)

DETECTION_CONF_THRESHOLD = 0.5
RECOGNITION_CONF_THRESHOLD = 0.5
CHAR_LIST = "#0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ "


class Application(rh.BaseDepthAIApplication):
    def setup_pipeline(self) -> dai.Pipeline:
        """Define the pipeline using DepthAI."""

        log.info(f"App config: {rh.CONFIGURATION}")

        pipeline = dai.Pipeline()
        version = "2021.2"
        pipeline.setOpenVINOVersion(version=dai.OpenVINO.Version.VERSION_2021_2)

        color_cam: dai.node.ColorCamera = pipeline.create(dai.node.ColorCamera)
        color_cam.setPreviewSize(NN_SIZE)
        color_cam.setVideoSize(CAM_SIZE)
        color_cam.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
        color_cam.setInterleaved(False)
        color_cam.setBoardSocket(dai.CameraBoardSocket.RGB)
        color_cam.setFps(rh.CONFIGURATION["fps"])

        h264_encoder: dai.node.VideoEncoder = pipeline.create(dai.node.VideoEncoder)
        h264_encoder.setDefaultProfilePreset(
            color_cam.getFps(), dai.VideoEncoderProperties.Profile.H264_MAIN
        )
        color_cam.video.link(h264_encoder.input)

        nn = pipeline.create(dai.node.NeuralNetwork)
        nn.setBlobPath(
            blobconverter.from_zoo(
                name="east_text_detection_256x256",
                zoo_type="depthai",
                shaves=6,
                version=version,
            )
        )
        color_cam.preview.link(nn.input)
        xin: dai.node.XLinkIn = pipeline.createXLinkIn()
        xin.setStreamName("color_control_in")
        xin.out.link(color_cam.inputControl)

        create_output(pipeline, nn.out, "nn_out")
        create_output(pipeline, color_cam.video, "color_out")
        create_output(pipeline, h264_encoder.bitstream, "h264_out")
        create_output(pipeline, color_cam.still, "color_still_out")

        return pipeline

    def manage_device(self, device: dai.Device):
        reader = easyocr.Reader(["en"])
        h264_queue: dai.DataOutputQueue = device.getOutputQueue(
            "h264_out", maxSize=30, blocking=False
        )
        color_queue: dai.DataOutputQueue = device.getOutputQueue(
            "color_out", maxSize=30, blocking=False
        )
        nn_queue: dai.DataOutputQueue = device.getOutputQueue(
            "nn_out", maxSize=30, blocking=False
        )
        color_still_queue: dai.DataOutputQueue = device.getOutputQueue(
            "color_still_out", maxSize=30, blocking=False
        )

        color_control_in_queue: dai.DataInputQueue = device.getInputQueue(
            "color_control_in"
        )

        live_view = rh.DepthaiLiveView("Live view", "live_view", *CAM_SIZE)
        while rh.app_is_running():
            h264_packet: dai.ImgFrame = h264_queue.get()
            color_packet: dai.ImgFrame = color_queue.get()
            nn_packet: dai.NNData = nn_queue.get()
            color_still: dai.ImgFrame | None = color_still_queue.tryGet()
            color_frame = color_packet.getCvFrame().copy()

            boxes, angles = east.decode_east(nn_packet, RECOGNITION_CONF_THRESHOLD)
            rotated_rect_points = [
                east.get_rotated_rect_points(bbox, angle * -1)
                for (bbox, angle) in zip(boxes, angles)
            ]

            horizontal_boxes = []
            for rp in rotated_rect_points:
                # Detections are done on 256x256 frames, we are sending back 1024x1024
                # That's why we rescale points
                scaling = np.asarray(CAM_SIZE) / np.asarray(NN_SIZE)
                scaled_points = np.intp(rp * scaling)

                min_x = np.min(scaled_points[:, 0])
                min_y = np.min(scaled_points[:, 1])
                max_x = np.max(scaled_points[:, 0])
                max_y = np.max(scaled_points[:, 1])

                hor_box = [min_x, max_x, min_y, max_y]
                horizontal_boxes.append(hor_box)

            results = reader.recognize(
                color_frame,
                horizontal_list=horizontal_boxes,
                free_list=[],
                allowlist=CHAR_LIST,
                decoder="beamsearch",
            )
            for res in results:
                bbox, text, conf = res
                if conf > RECOGNITION_CONF_THRESHOLD:
                    bbox_formatted = bbox[0] + bbox[2]

                    live_view.add_rectangle(bbox_formatted, "")
                    live_view.add_text(
                        text.upper(), (bbox[0][0], bbox[0][1] - 3), 1, (255, 255, 255)
                    )

            live_view.publish(h264_packet.getCvFrame())


if __name__ == "__main__":
    app = Application()
    app.run()
