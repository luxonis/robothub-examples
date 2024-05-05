import logging as log

import depthai as dai


__all__ = ["FindStart"]


class FindStart:
    """First messages are dropped somehow, need to find the first complete sequence of nn results."""
    _find_start = True

    def __init__(self, sequence_length: int):
        self._sequence_length_mem = {}
        self._sequence_length = sequence_length

    def __call__(self, message: dai.ImgDetections | dai.ImgFrame):
        log.debug(f"{self._find_start=},  {self._sequence_length_mem=}")
        if self._find_start:
            if message.getSequenceNum() not in self._sequence_length_mem:
                self._sequence_length_mem[message.getSequenceNum()] = 1
            else:
                self._sequence_length_mem[message.getSequenceNum()] += 1
                if self._sequence_length_mem[message.getSequenceNum()] == self._sequence_length:
                    self._find_start = False
                    self._sequence_length_mem.pop(message.getSequenceNum())
                    self._sequence_length_mem.clear()
        else:
            return True

    @classmethod
    def reset(cls):
        log.warning("Resetting FindStart")
        cls._find_start = True
