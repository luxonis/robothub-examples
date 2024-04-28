__all__ = ["BoundingBox"]


class BoundingBox:
    """
    Represents a bounding box in relative coordinates
    xmin, xmax, ymin, ymax are in [0;1], values > 1 are set to 1 and values < 0 are set to 0
    """

    def __init__(self, xmin: float, xmax: float, ymin: float, ymax: float, confidence: float, image_height: int, image_width: int,
                 sequence_number: int = 0):
        self.frame_sequence_number: int = sequence_number
        self.label = ""

        self.confidence = confidence

        self.xmin_relative, self.ymin_relative, self.xmax_relative, self.ymax_relative = \
            self.correct(xmin, ymin, xmax, ymax)

        self.x_avg_relative = (self.xmax_relative + self.xmin_relative) / 2  # relative size
        self.y_avg_relative = (self.ymin_relative + self.ymax_relative) / 2  # relative size

        self.height = image_height
        self.width = image_width

        # check max points are really bigger then min points
        if self.xmax_relative < self.xmin_relative:
            raise ValueError(f"{xmax=} is smaller then {xmin=}")
        if self.ymax_relative < self.ymin_relative:
            raise ValueError(f"{ymax=} is smaller then {ymin=}")

        self.xmin = int(self.xmin_relative * self.width)
        self.xmax = int(self.xmax_relative * self.width)
        self.ymin = int(self.ymin_relative * self.height)
        self.ymax = int(self.ymax_relative * self.height)
        self.x_avg = int(self.x_avg_relative * self.width)
        self.y_avg = int(self.y_avg_relative * self.height)

    def __str__(self):
        return f"BBox: xmin:{self.xmin}, xmax:{self.xmax}," \
               f" ymin:{self.ymin}, ymax:{self.ymax}"

    def set_label(self, label: str):
        self.label = label

    @classmethod
    def from_absolute(cls, xmin: int, xmax: int, ymin: int, ymax: int, confidence: float, image_width: int, image_height: int,
                      sequence_number: int = 0):
        return cls(xmin=xmin / image_width, xmax=xmax / image_width, ymin=ymin / image_height, ymax=ymax / image_height,
                   confidence=confidence, image_height=image_height, image_width=image_width, sequence_number=sequence_number)

    def getSequenceNum(self) -> int:
        return self.frame_sequence_number

    @staticmethod
    def correct(xmin, ymin, xmax, ymax) -> tuple:
        xmin = clamp(num=xmin, minimum=0.001, maximum=0.996)
        ymin = clamp(num=ymin, minimum=0.001, maximum=0.996)
        xmax = clamp(num=xmax, minimum=xmin + 0.001, maximum=0.999)
        ymax = clamp(num=ymax, minimum=ymin + 0.001, maximum=0.999)
        return xmin, ymin, xmax, ymax

    def as_nms_box(self):
        """Defined as xmin, ymin, width, height. In absolute coordinates."""
        return self.xmin, self.ymin, self.xmax - self.xmin, self.ymax - self.ymin

    def transform(self, width: int, height: int) -> tuple[int, int, int, int]:
        """Transforms bounding box to different image size.

        :param width: width of the new image
        :param height: height of the new image
        :returns: tuple(xmin, ymin, xmax, ymax) with respect to the new image size.
        """

        larger_side_current = max(self.height, self.width)
        shorter_side_current = min(self.height, self.width)
        larger_side_new = max(width, height)
        shorter_side_new = min(width, height)

        scaling_factor = larger_side_current / larger_side_new
        letter_box_offset = (shorter_side_new - (shorter_side_current / scaling_factor)) / 2

        xmin_nn_out = int(self.xmin / scaling_factor)
        xmax_nn_out = int(self.xmax / scaling_factor)
        ymin_nn_out = int(self.ymin / scaling_factor + letter_box_offset)
        ymax_nn_out = int(self.ymax / scaling_factor + letter_box_offset)
        # print(f"{xmin_nn_out = }, {xmax_nn_out = }, {ymin_nn_out = }, {ymax_nn_out = }")

        return xmin_nn_out, ymin_nn_out, xmax_nn_out, ymax_nn_out


def clamp(num, minimum, maximum):
    return max(minimum, min(num, maximum))
