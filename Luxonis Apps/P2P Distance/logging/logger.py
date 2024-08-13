import os
from datetime import datetime

class Logger:
    def __init__(self):
        self.log_dir = None
        self.logging = False
        self.counter = 0
        self._init_log_file()

    def _init_log_file(self):
        today = datetime.now().strftime('%d.%m.%Y')
        log_dir = os.path.join('logs', today)

        counter = 1
        unique_log_dir = log_dir
        # while os.path.exists(unique_log_dir):
        #     unique_log_dir = f"{log_dir}_{counter}"
        #     counter += 1

        # os.makedirs(unique_log_dir)
        self.log_dir = unique_log_dir

    def start_logging(self):
        self.logging = True

    def stop_logging(self):
        self.logging = False

    def toggle_logging(self):
        self.logging = not self.logging

    def log(self, file, message, add_header=False):
        file_path = os.path.join(self.log_dir, f"{file}.txt")
        with open(file_path, 'a') as f:
            if add_header and os.path.getsize(file_path) == 0:
                header = "Time Calculated_Distance Actual_Distance Error Mode\n"
                f.write(header)
            f.write(message + '\n')

    def log_distance(self, point1_distance, point2_distance, calculated_distance, actual_distance=None, mode=None):
        if not self.logging:
            return

        file_name = f"{int(point1_distance)}cm_{int(point2_distance)}cm"

        # Log format: Time, Depth point 1, Depth point 2, Calculated Distance, Actual Distance, Error, Mode
        timestamp = datetime.now().strftime('%H:%M:%S')

        # Calculate error if actual distance is provided
        if actual_distance is not None:
            error = abs(calculated_distance - actual_distance)
        else:
            error = 'Null'

        # Construct log entry with necessary details, separated by spaces
        log_entry = f"{timestamp} {calculated_distance} {actual_distance if actual_distance else ''} {error} {mode if mode else 'Null'}"

        # Log the entry, adding a header if it's the first time the file is being written to
        self.log(file_name, log_entry, add_header=True)
        self.counter += 1

        if self.counter == 500:
            self.logging = False
            self.counter = 1
