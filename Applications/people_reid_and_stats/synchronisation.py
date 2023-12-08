
import logging as log


class Synchronizer:

    def __init__(self, number_of_messages_per_sequence_number: int):
        self.__callbacks = []
        self.__msgs = {}
        self.__number_of_messages_per_sequence_number = number_of_messages_per_sequence_number

    def add_callback(self, callback: callable):
        self.__callbacks.append(callback)

    def add_message(self, message: any, sequence_number: int, identifier: str):
        if sequence_number not in self.__msgs:
            self.__msgs[sequence_number] = {}
        self.__msgs[sequence_number][identifier] = message

        if len(self.__msgs[sequence_number]) == self.__number_of_messages_per_sequence_number:
            messages: dict = self.__msgs.pop(sequence_number)
            self.__send_synchronized_messages(messages)
        # remove older sequence_numbers
        keys_to_remove = []
        for sequence_number_memory in self.__msgs.keys():
            if sequence_number_memory < sequence_number:
                keys_to_remove.append(sequence_number_memory)
        # remove old keys
        for key in keys_to_remove:
            log.debug(f"Removing sequence number {key} from memory")
            self.__msgs.pop(key)
        # make sure memory doesn't get too long
        if len(self.__msgs) > 200:
            log.error(f"Too many sequence numbers in memory removing first 10")
            for _ in range(10):
                self.__msgs.pop(list(self.__msgs.keys())[0])

    def __send_synchronized_messages(self, messages: dict):
        for callback in self.__callbacks:
            callback(messages)



