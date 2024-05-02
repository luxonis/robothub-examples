import logging as log

import depthai as dai


__all__ = ["FindStart"]


class FindStart:
    """First messages are dropped somehow, need to find the first complete sequence of nn results."""

    def __init__(self, sequence_length: int):
        self._find_start = True
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
        else:
            return True
