import logging as log

from app_pipeline import host_node
from app_pipeline.controlls import Control
from app_pipeline.messages import Message, ControlMessage


class Switch(host_node.BaseNode):

    def __init__(self, input_node: host_node.BaseNode, name: str):
        super().__init__()
        input_node.set_callback(callback=self.__callback)
        self._name = name
        self._flick_switch_on = False
        self._flick_switch_triggered = False
        self._switch_on = False
        self._last_message_after_switch_off_sent = True
        self._passthrough = False

    def __callback(self, message: Message) -> None:
        if self._passthrough:
            self.send_message(message=ControlMessage(control=Control.TURN_OFF, message=message))
        elif self._flick_switch_on:
            if self._flick_switch_triggered:
                self._flick_switch_triggered = False
                self._toggle_flick_switch()
                self.send_message(message=ControlMessage(control=Control.TURN_OFF, message=message))
            else:
                self.send_message(message=ControlMessage(control=Control.TURN_ON, message=message))
        elif self._flick_switch_triggered:
            self._flick_switch_triggered = False
            self._toggle_flick_switch()
            self.send_message(message=ControlMessage(control=Control.TURN_OFF, message=message))
        elif self._switch_on:
            self.send_message(message=ControlMessage(control=Control.TURN_ON, message=message))
        elif self._send_last_message_after_switch_off:
            self._last_message_after_switch_off_sent = True
            self.send_message(message=ControlMessage(control=Control.TURN_OFF, message=message))

    def flick_switch(self) -> None:
        log.info(f"Flick switch {self._name} is triggered.")
        self._flick_switch_triggered = True
        self._toggle_flick_switch()

    def switch_on(self) -> None:
        self._switch_on = True
        log.info(f"Switch {self._name} is now on.")

    def switch_off(self) -> None:
        if not self._switch_on:
            log.warning(f"Switch {self._name} is already off.")
            return
        self._switch_on = False
        self._last_message_after_switch_off_sent = False
        log.info(f"Switch {self._name} is now off.")

    def flick_switch_on(self) -> None:
        self._flick_switch_on = True
        log.info(f"Flick switch {self._name} is now on.")

    def flick_switch_off(self) -> None:
        self._flick_switch_on = False
        log.info(f"Flick switch {self._name} is now off.")

    def passthrough_on(self) -> None:
        self._passthrough = True
        log.info(f"Passthrough {self._name} is now on.")

    def passthrough_off(self) -> None:
        self._passthrough = False
        log.info(f"Passthrough {self._name} is now off.")


    def _toggle_flick_switch(self) -> None:
        if self._flick_switch_on is True:
            self._flick_switch_on = False
            log.info(f"Flick switch {self._name} is now off.")
        else:
            self._flick_switch_on = True
            log.info(f"Flick switch {self._name} is now on.")

    @property
    def _send_last_message_after_switch_off(self) -> bool:
        return not self._switch_on and not self._last_message_after_switch_off_sent
