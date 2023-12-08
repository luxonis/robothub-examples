from enum import Enum, auto
from typing import List, Tuple

import cv2

def clamp(num, v0, v1):
    return max(v0, min(num, v1))


class Region(Enum):
    OUT = auto()
    IN = auto()
    UNDECIDED = auto()


class Point:
    """ Internally works with standard cartesian x,y system, but returns x,y coordinates in image frame sense,
        y coordinate positive direction points down."""
    x: int
    y: int
    z: float

    def __init__(self, x: int, y: int, z: float = 0.):
        self.__setattr__("x", x)
        self.__setattr__("y", y)
        self.__setattr__("z", z)

    def __setattr__(self, key, value):
        assert value is not None
        if key == "y":
            value = -value
        self.__dict__[key] = value

    def __getattr__(self, item):
        raise ValueError(f"{item = } is not valid class attribute")

    def __str__(self):
        return f"({self.__dict__['x']}, {-self.__dict__['y']}, {self.__dict__['z']})"

    @property
    def get_x(self):
        return self.__dict__["x"]

    @property
    def get_y(self):
        return - self.__dict__["y"]

    @property
    def get_z(self):
        return self.__dict__["z"]

    @property
    def get_point(self) -> Tuple:
        """Return point value as tuple."""

        return self.__dict__["x"], -self.__dict__["y"]

    @staticmethod
    def create_point(coordinates: Tuple):
        z = 0.
        if len(coordinates) == 2:
            x, y = coordinates
        elif len(coordinates) == 3:
            x, y, z = coordinates
        else:
            raise ValueError(f"coordinates must contain either x, y or x, y, z but contain {coordinates = }")

        return Point(x=x, y=y, z=z)


class Border:
    """Handles everything regarding boarder line. Boarder line is of form: y = ax + b and splits frame in two regions. Region OUT and IN."""

    # TODO: init from config? or based on real image?
    FRAME_HEIGHT = 1080
    FRAME_WIDTH = 1980

    def __init__(self, p1: Point, p2: Point, depth: float, out_above: bool = True):
        """Initialize border class.
        :param p1: Point on the boarder line
        :param p2: Point on the boarder line different to p1
        :param depth: Borderline distance from camera
        :param out_above: area above boarder line is OUT if out_above is True, IN otherwise.
        """

        self.out_above = out_above
        self.p1 = p1
        self.p2 = p2
        self.depth = depth
        self.a = 0.
        self.b = 0.

        self.calculate_line_coefficients()

    def __str__(self):
        return f"y = {self.a}x + {self.b}"

    def calculate_line_coefficients(self) -> None:
        """Calculate parameters a,b of y=ax+b from two points p1, p2. Using real coordinates p.x, p.y."""

        self.a = (self.p1.y - self.p2.y) / (self.p1.x - self.p2.x)
        self.b = self.p2.y - self.p2.x * self.a

    def __solve_for_y(self, x: int) -> int:
        """Solve y=ax+b for y and return as index."""

        return int(self.a * x + self.b)

    def __solve_for_x(self, y: int) -> int:
        """Solve y=ax+b for x and return as index."""

        assert (self.a != 0)
        return int((y - self.b) / self.a)

    def get_point_region(self, point: Point, point_depth: float = 0.) -> Region:
        """Get point position with respect to the boarder line."""

        if self.a == 0:
            if point.y < self.b:  # and point_depth < self.depth
                return Region.IN if self.out_above else Region.OUT
            return Region.OUT if self.out_above else Region.IN
        border_x = self.__solve_for_x(y=point.y)
        border_y = self.__solve_for_y(x=point.x)

        if self.a > 0:
            if point.x <= border_x and point.y >= border_y:  # and point_depth > self.depth
                return Region.OUT if self.out_above else Region.IN
            if point.x > border_x and point.y < border_y:
                return Region.IN if self.out_above else Region.OUT
            print(f"Could not decide.")
            return Region.UNDECIDED

        if self.a < 0:
            if point.x >= border_x and point.y >= border_y:  # and point_depth > self.depth
                return Region.OUT if self.out_above else Region.IN
            if point.x < border_x and point.y < border_y:
                return Region.IN if self.out_above else Region.OUT
            print(f"Could not decide.")
            return Region.UNDECIDED

    def __get_line_endpoints(self) -> Tuple[Point, Point]:
        """Get two points where borderline crosses image frame borders."""

        if self.a == 0:
            return Point(x=0, y=int(self.b)), Point(x=self.FRAME_WIDTH, y=int(self.b))
        if self.a > 0:
            possible_x_left = self.__solve_for_x(y=0)
            if possible_x_left >= 0:
                x_left = possible_x_left
                y_left = 0
            else:
                x_left = 0
                y_left = self.__solve_for_y(x=0)
            possible_x_right = self.__solve_for_x(y=-self.FRAME_HEIGHT)  # convert to real coordinates
            if possible_x_right <= self.FRAME_WIDTH:
                x_right = possible_x_right
                y_right = self.FRAME_HEIGHT
            else:
                x_right = self.FRAME_WIDTH
                y_right = self.__solve_for_y(x=self.FRAME_WIDTH)
            return Point(x=x_left, y=y_left), Point(x=x_right, y=y_right)

        if self.a < 0:
            possible_x_left = self.__solve_for_x(y=-self.FRAME_HEIGHT)
            if possible_x_left >= 0:
                x_left = possible_x_left
                y_left = self.FRAME_HEIGHT
            else:
                y_left = self.__solve_for_y(x=0)
                x_left = 0
            possible_x_right = self.__solve_for_x(y=0)
            if possible_x_right <= self.FRAME_WIDTH:
                x_right = possible_x_right
                y_right = 0
            else:
                x_right = self.FRAME_WIDTH
                y_right = self.__solve_for_y(x=self.FRAME_WIDTH)
            return Point(x=x_left, y=y_left), Point(x=x_right, y=y_right)

    def draw_borderline(self, image, color: Tuple[int, int, int] = (0, 0, 255)):
        """Draw borderline in the image."""

        start_point, end_point = self.__get_line_endpoints()
        thickness = 2
        return cv2.line(image, start_point.get_point, end_point.get_point, color, thickness)


class RoiFromBorderLanes:
    """Represents a ROI defined by lines (Border class).
    ROI is defined as Region.IN interception of all lines, i.e. only region where all lines define Region.IN is in ROI.
    """

    def __init__(self, borders: List[Border]):
        self.borders = borders

    def __str__(self):
        text = ""
        for border in self.borders:
            text += f"{border}\n"

    def is_inside_lane(self, point: Point, point_depth: float = 0.) -> bool:
        for border in self.borders:
            region = border.get_point_region(point=point, point_depth=point_depth)
            if region == Region.OUT:
                return False
        return True

    def draw_borders(self, image, color: tuple[int, int, int] = (0, 255, 0)):
        for border in self.borders:
            image = border.draw_borderline(image=image, color=color)
        return image


class BoundingBox:
    """
    Represents a bounding box in relative coordinates
    xmin, xmax, ymin, ymax are in [0;1], values > 1 are set to 1 and values < 0 are set to 0
    """

    def __init__(self, xmin: float, xmax: float, ymin: float, ymax: float, confidence: float, image_height: int, image_width: int):
        self.id: int = -1

        self.confidence = confidence

        self.xmin_relative = clamp(xmin, 0, 1)
        self.xmax_relative = clamp(xmax, 0, 1)
        self.ymin_relative = clamp(ymin, 0, 1)
        self.ymax_relative = clamp(ymax, 0, 1)

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

    def to_dict(self):
        return {"xmin": self.xmin, "xmax": self.xmax, "ymin": self.ymin, "ymax": self.ymax}

    @property
    def middle(self) -> Tuple[int, int]:
        """Get coordinates of bounding box middle.

        :returns: tuple representing the middle point, (x, y)
        """

        return self.x_avg, self.y_avg

    @property
    def bottom_middle(self) -> Tuple[int, int]:
        """Get middle point of the top bbox line.
        :returns: tuple representing the middle point, (x, y)
        """
        return self.x_avg, self.ymax

    @property
    def bottom_middle_relative(self) -> Tuple[float, float]:
        """Get middle point of the top bbox line.
        :returns: tuple representing the middle point, (x, y)
        """
        return self.x_avg_relative, self.ymax_relative

    @property
    def top_middle(self) -> Tuple[int, int]:
        """Get middle point of the top bbox line.
        :returns: tuple representing the middle point, (x, y)
        """

        return self.x_avg, self.ymin

    @property
    def area(self):

        delta_x = (self.xmax - self.xmin)
        delta_y = (self.ymax - self.ymin)
        return delta_x * delta_y

    @property
    def absolute(self) -> Tuple[int, int, int, int]:
        """Get tuple representation in absolute coordinates."""

        return self.xmin, self.ymin, self.xmax, self.ymax

    @property
    def relative(self) -> Tuple[float, float, float, float]:
        """Get tuple representation in relative coordinates."""

        return self.xmin_relative, self.ymin_relative, self.xmax_relative, self.ymax_relative

    def get_point_region(self, point: Point):
        """Point is expected to contain absolute coordinates."""

        if self.xmin <= point.get_x <= self.xmax and self.ymin <= point.get_y <= self.ymax:
            return Region.IN
        return Region.OUT

    def get_vertical_line_region(self, x: int, ymin: int, ymax: int):
        """If any part of the line is inside the bounding box return Region.IN."""

        if self.xmin <= x <= self.xmax:
            # line starts above ROI and ends inside or outside
            if ymin <= self.ymin <= ymax:
                return Region.IN
            # ymin or ymax inside the ROI
            if self.ymin <= ymin <= self.ymax or self.ymin <= ymax <= self.ymax:
                return Region.IN
        return Region.OUT

    def get_point_region_based_on_line(self, point: Point, which_line: str, above_line_is_out: bool):
        """
        Determine whether point lies above or below the upper bbox line.
        which_line: is one of: (N, W, S, E)
        out_above: The region above chosen line is the OUT region. For vertical lines above means LEFT
        """

        lines = {"N": self.__get_point_region_north_lane, "W": self.__get_point_region_west_lane, "S": self.__get_point_region_south_lane,
                 "E": self.__get_point_region_east_lane, "M": self.__get_point_region_middle_lane}
        chosen_line_region = lines.get(which_line, self.__get_point_region_north_lane)
        return chosen_line_region(point=point, above_line_is_out=above_line_is_out)

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

    def __get_point_region_north_lane(self, point: Point, above_line_is_out: bool):
        if self.xmin <= point.get_x <= self.xmax:
            if point.get_y >= self.ymin:
                return Region.IN if above_line_is_out else Region.OUT
            else:
                return Region.OUT if above_line_is_out else Region.IN
        return Region.UNDECIDED

    def __get_point_region_south_lane(self, point: Point, above_line_is_out: bool):
        if self.xmin <= point.get_x <= self.xmax:
            if point.get_y >= self.ymax:
                return Region.IN if above_line_is_out else Region.OUT
            else:
                return Region.OUT if above_line_is_out else Region.IN
        return Region.UNDECIDED

    def __get_point_region_middle_lane(self, point: Point, above_line_is_out: bool):
        if self.xmin <= point.get_x <= self.xmax:
            if point.get_y >= self.y_avg:
                return Region.IN if above_line_is_out else Region.OUT
            else:
                return Region.OUT if above_line_is_out else Region.IN
        return Region.UNDECIDED

    def __get_point_region_west_lane(self, point: Point, above_line_is_out: bool):
        if self.ymin <= point.get_y <= self.ymax:
            if point.get_x >= self.xmin:
                return Region.IN if above_line_is_out else Region.OUT
            else:
                return Region.OUT if above_line_is_out else Region.IN
        return Region.UNDECIDED

    def __get_point_region_east_lane(self, point: Point, above_line_is_out: bool):
        if self.ymin <= point.get_y <= self.ymax:
            if point.get_x >= self.xmax:
                return Region.IN if above_line_is_out else Region.OUT
            else:
                return Region.OUT if above_line_is_out else Region.IN
        return Region.UNDECIDED


def calculate_overlap_area(larger_bbox: BoundingBox, smaller_bbox: BoundingBox) -> float:
    x_left = max(smaller_bbox.xmin, larger_bbox.xmin)
    x_right = min(smaller_bbox.xmax, larger_bbox.xmax)
    y_top = max(smaller_bbox.ymin, larger_bbox.ymin)
    y_bottom = min(smaller_bbox.ymax, larger_bbox.ymax)
    if x_right > x_left and y_bottom > y_top:
        # Calculate overlap area
        overlap_area = (x_right - x_left) * (y_bottom - y_top)
        return overlap_area
    else:
        # No overlap
        return 0.

