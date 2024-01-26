import logging

class Log:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.handler = logging.FileHandler("./logs/app.log")
        self.formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s")
        self.handler.setFormatter(self.formatter)
        self.logger.addHandler(self.handler)
    
    def info(self, msg: str):
        self.logger.info(msg)
    def error(self, msg: str):
        self.logger.error(msg)