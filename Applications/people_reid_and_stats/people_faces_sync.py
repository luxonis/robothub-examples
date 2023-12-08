import depthai as dai
import logging as log

from base_node import BaseNode
from collections import deque
from geometry import BoundingBox, calculate_overlap_area
from messages import FaceData, FaceFeature, Person, PersonFiguresMessage, PeopleFacesMessage
from synchronisation import Synchronizer


class PeopleFacesSync(BaseNode):

    def __init__(self, people_tracking: BaseNode, face_features: BaseNode):
        super().__init__()
        people_tracking.set_callback(self.people_tracking_callback)
        face_features.set_callback(self.face_features_callback)
        self.__person_memory: dict[int, Person] = {}
        self.__person_age_memory: dict[int, deque[int]] = {}
        self.__synchronizer = Synchronizer(number_of_messages_per_sequence_number=2)
        self.__synchronizer.add_callback(self.__update_faces)

    def people_tracking_callback(self, message: PersonFiguresMessage):
        self.__remove_people_from_memory(message=message)
        self.__update_figures(message=message)
        # update faces if possible
        self.__synchronizer.add_message(message=message, sequence_number=message.sequence_number, identifier="person_figures")
        self.__send_message(message=message)

    def face_features_callback(self, message: FaceData):
        self.__synchronizer.add_message(message=message, sequence_number=message.sequence_number, identifier="face_data")

    def __remove_people_from_memory(self, message: PersonFiguresMessage) -> None:
        active_ids = []
        for figure in message.person_figures:
            active_ids.append(figure.tracking_id)
        for id_in_memory in list(self.__person_memory.keys()):
            if id_in_memory not in active_ids:
                del self.__person_memory[id_in_memory]

    def __update_figures(self, message: PersonFiguresMessage):
        """Update only already existing people in memory."""
        for figure in message.person_figures:
            if figure.tracking_id in self.__person_memory:
                person = self.__person_memory[figure.tracking_id]
                person.figure = figure
            else:
                person = Person(figure=figure, face_features=None)
                self.__person_memory[figure.tracking_id] = person

    def __update_faces(self, messages: dict) -> None:
        person_figures_data: PersonFiguresMessage = messages["person_figures"]
        face_features: FaceData = messages["face_data"]
        for face_feature in face_features.data:
            face_bbox = face_feature.bbox
            largest_overlap_area = 0.
            best_person_match = None
            for person_figure in person_figures_data.person_figures:
                overlap_area = calculate_overlap_area(larger_bbox=person_figure.bbox, smaller_bbox=face_bbox)
                if overlap_area > largest_overlap_area:
                    largest_overlap_area = overlap_area
                    best_person_match = person_figure
            if largest_overlap_area > face_bbox.area * 0.5:
                # get person from memory. it has to be there because of the __update_figures() call that comes first
                person = self.__person_memory[best_person_match.tracking_id]
                # update age buffer
                age_memory = self.__person_age_memory.get(best_person_match.tracking_id, deque(maxlen=30))
                age_memory.append(face_feature.age)
                self.__person_age_memory[best_person_match.tracking_id] = age_memory
                # calculate average age
                average_age = sum(age_memory) // len(age_memory)
                # update objects
                face_feature.age = average_age
                person.face_features = face_feature

    def __send_message(self, message: PersonFiguresMessage) -> None:
        message = PeopleFacesMessage(people=list(self.__person_memory.values()), image=message.rgb_image)
        self.send_message(message=message)
