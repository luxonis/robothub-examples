

class BaseNode:
    def __init__(self):
        self.callbacks = []

    def set_callback(self, callback: callable):
        self.callbacks.append(callback)

    def send_message(self, message):
        for callback in self.callbacks:
            callback(message)
