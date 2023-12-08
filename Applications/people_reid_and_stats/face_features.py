import depthai as dai
import numpy as np

from base_node import BaseNode
from geometry import BoundingBox
from messages import FaceData, FaceFeature

EMOTIONS = ['neutral', 'happy', 'sad', 'surprise', 'anger']


class FaceFeatures(BaseNode):

    def __init__(self, age_gender_queue: dai.DataOutputQueue, emotions_queue: dai.DataOutputQueue):
        super().__init__()
        self.__age_gender_queue = age_gender_queue
        self.__emotions_queue = emotions_queue

    def face_features_callback(self, face_detections_frame: dai.ImgDetections):
        number_of_faces = len(face_detections_frame.detections)
        if number_of_faces == 0:
            return
        age_data, gender_data, emotions_data = self.fetch_pipeline_outputs(data_count=number_of_faces)
        data = [FaceFeature(age=age, gender=gender, emotion=emotion, bbox=self.__get_bbox(face_detection)) for
                face_detection, age, gender, emotion in zip(face_detections_frame.detections, age_data, gender_data, emotions_data)]
        face_features: FaceData = FaceData(data=data, sequence_number=face_detections_frame.getSequenceNum())
        self.send_message(message=face_features)  # send data to the next node

    def fetch_pipeline_outputs(self, data_count: int):
        age_data = []
        gender_data = []
        emotions_data = []
        re_id_data = []
        counter = 0
        while True:
            age_gender_frame: dai.NNData = self.__age_gender_queue.get()
            emotions_frame: dai.NNData = self.__emotions_queue.get()
            age, gender = self.__decode_age_gender(age_gender_frame=age_gender_frame)
            age_data.append(age)
            gender_data.append(gender)
            emotions_data.append(self.__decode_emotions(emotions_frame=emotions_frame))
            counter += 1
            if counter == data_count:
                break
        return age_data, gender_data, emotions_data

    @staticmethod
    def __decode_age_gender(age_gender_frame: dai.NNData):
        age = int(float(np.squeeze(np.array(age_gender_frame.getLayerFp16('age_conv3')))) * 100)
        gender = np.squeeze(np.array(age_gender_frame.getLayerFp16('prob')))
        gender_str = "Woman" if gender[0] > gender[1] else "Man"
        return age, gender_str

    @staticmethod
    def __decode_emotions(emotions_frame: dai.NNData):
        emotion_results = np.array(emotions_frame.getFirstLayerFp16())
        emotion_name = EMOTIONS[np.argmax(emotion_results)]
        return emotion_name

    def __get_bbox(self, detection: dai.ImgDetection):
        fd = detection
        face_bbox = BoundingBox(xmin=fd.xmin, xmax=fd.xmax, ymin=fd.ymin, ymax=fd.ymax, image_width=1920, image_height=1080,
                                confidence=fd.confidence)
        return face_bbox
