from functools import partial

from app_pipeline import host_node, synchronization

__all__ = ["Sync"]


class Sync(host_node.BaseNode):
    """General Sync Node."""

    def __init__(self, inputs: list[host_node.BaseNode], input_names: list[str], output_message_obj):
        super().__init__()
        self._output_message_obj = output_message_obj
        self._wait_for_messages_nr = len(inputs)
        self._synchronizer = synchronization.Synchronizer(number_of_messages_per_sequence_number=self._wait_for_messages_nr)
        self._synchronizer.add_callback(self._process_synced_messages)
        for _input, input_name in zip(inputs, input_names):
            _input.set_callback(callback=partial(self.__callback, input_name))

    def __callback(self, input_name, message):
        self._synchronizer.add_message(message=message, sequence_number=message.getSequenceNum(), identifier=input_name)

    def _process_synced_messages(self, messages: dict):
        self.send_message(message=self._output_message_obj(**messages))
