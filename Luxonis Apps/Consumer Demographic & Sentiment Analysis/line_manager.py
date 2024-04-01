import json
import logging as log
import os
import pathlib
import robothub
import threading
import toml


class LineManager:

    def __init__(self):
        self.lines: dict = self.init_lines()
        self.config = robothub.CONFIGURATION

        # Autosave
        self.autosave_interval = 5  # Seconds
        self.autosave_timer = None
        self.start_autosave()

        robothub.COMMUNICATOR.on_frontend(notification=self.on_fe_notification, request=self.on_fe_request)

    @property
    def line_entities(self):
        return self.lines["entities"]

    def start_autosave(self):
        self.save_lines()
        self.autosave_timer = threading.Timer(self.autosave_interval, self.start_autosave)
        self.autosave_timer.start()

    def save_lines(self):
        if robothub.LOCAL_DEV:
            lines_path = "data/lines.json"
        else:
            lines_path = "/storage/lines.json"

        with open(lines_path, "w") as json_file:
            json.dump({"entities": self.lines["entities"]}, json_file)

    def init_lines(self):
        tmp_lines = {"entities": []}

        # Load data from file
        lines_path = "/storage/lines.json"
        if os.path.exists(lines_path):
            with open(lines_path, "r") as json_file:
                data = json.load(json_file)
                tmp_lines["entities"] = data["entities"]
            log.info(f"Loaded line entities from JSON: {data}")

        return tmp_lines

    def on_fe_request(self, session_id, unique_key, payload):
        if "get_config_structure" in unique_key:
            return {"result": self.get_config_structure()}
        elif "get_config" in unique_key:
            return {"result": self.get_confg()}
        elif "get_lines" in unique_key:
            return {"result": self.lines}
        elif "export_lines" in unique_key:
            return {"result": self.export_lines()}

    def on_fe_notification(self, session_id, unique_key, payload):
        if "set_config" in unique_key:
            self.set_config(payload)
        elif "create_line" in unique_key:
            self.create_line(payload=payload)
        elif "update_line" in unique_key:
            self.update_line(payload=payload)
        elif "reset_line" in unique_key:
            self.reset_line(payload=payload)
        elif "toggle_line" in unique_key:
            self.toggle_line(payload=payload)
        elif "delete_line" in unique_key:
            self.delete_line(payload=payload)
        elif "import_lines" in unique_key:
            self.import_lines(payload=payload)

    def get_config_structure(self):
        with open("robotapp.toml", "r") as file:
            parsed_toml = toml.load(file)

        configurations = parsed_toml.get("configuration", [])
        configs_list = []
        for config in configurations:
            configs_list.append(config)

        return configs_list

    def get_confg(self):
        return {"robotId": os.environ["ROBOTHUB_ROBOT_ID"], "robotAppId": os.environ["ROBOTHUB_ROBOT_APP_ID"], **self.config}

    def set_config(self, payload):
        self.config.update(payload)

    def create_line(self, payload: dict):
        try:
            if 20 <= len(self.lines["entities"]):
                log.warning(f"Max number of lines has been exceeded")
            else:
                self.lines["entities"].append({
                    "id": payload["id"],
                    "trackLabelId": payload["trackLabelId"],
                    "detectionLabels": payload["detectionLabels"],
                    "isDisabled": False,
                    "count": 0,
                    "lastCrossAt": None,
                    "x1": payload["x1"],
                    "y1": payload["y1"],
                    "x2": payload["x2"],
                    "y2": payload["y2"]
                })
                log.info(f"New line created: {payload}")
        except Exception as e:
            log.error(f"Line creation failed: {e=}, {payload=}")

    def update_line(self, payload: dict):
        try:
            entities = self.lines["entities"]
            for entity in entities:
                if entity["id"] == payload["id"]:
                    entity.update({"x1": payload["x1"], "y1": payload["y1"], "x2": payload["x2"], "y2": payload["y2"]})
                    break

            log.info(f"Line updated: {payload=}")
        except Exception as e:
            log.error(f"Line update failed: {e=}, {payload=}")

    def reset_line(self, payload: dict):
        try:
            entities = self.lines["entities"]
            for entity in entities:
                if entity["id"] == payload:
                    entity.update({"count": 0, "lastCrossAt": None})
                    break

            log.info(f"Line restarted: {payload=}")
        except Exception as e:
            log.error(f"Line reset failed: {e=}, {payload=}")

    def toggle_line(self, payload: dict):
        try:
            entities = self.lines["entities"]
            for entity in entities:
                if entity["id"] == payload["id"]:
                    entity.update({"isDisabled": payload["isDisabled"]})
                    break

            log.info(f"Line toggled: {payload=}")
        except Exception as e:
            log.error(
                f"Line toggling failed: {e=}, {payload=}"
            )

    def delete_line(self, payload: dict):
        try:
            entities = self.lines["entities"]
            for entity in entities:
                if entity['id'] == payload:
                    entities.remove(entity)
                    break

            log.info(f"Line removed: {payload=}")
        except Exception as e:
            log.error(f"Line deletion failed: {e=}, {payload=}")

    def export_lines(self):
        log.info(f"Lines exported: {self.lines=}")
        return self.lines

    def import_lines(self, payload: dict):
        try:
            log.info(payload)
            self.lines = payload["data"]
            log.info(f"Lines imported: {payload=}")
        except Exception as e:
            log.error(f"Lines import failed: {e=}, {payload=}")
