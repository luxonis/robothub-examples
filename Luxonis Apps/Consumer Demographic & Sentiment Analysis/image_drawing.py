import cv2
import emoji
import numpy as np

from numpy import ndarray
from PIL import Image, ImageDraw, ImageFont


def draw_point(image: ndarray, point: tuple[int, int], color: tuple[int, int, int] = (255, 0, 0)):
    # accepts only rgb images
    assert len(image.shape) == 3
    cv2.circle(image, point, 3, color, 2)


def draw_text(image: ndarray, text: str, bottom_left_position: tuple[int, int], color: tuple[int, int, int] = (0, 0, 0), room_for_text: int = None):
    # cv2.putText(image, text, bottom_left_position, font, font_scale, color, thickness)
    font_scale = 0.8
    if room_for_text is not None:
        font_scale = _calculate_font_scale(text=text, desired_width=room_for_text)
    cv2.putText(image, text, bottom_left_position, cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 1)


def draw_rectangle(image: ndarray, bottom_left: tuple[int, int], top_right: tuple[int, int], color=(0, 255, 0), thickness=1):
    cv2.rectangle(img=image, pt1=bottom_left, pt2=top_right, color=color, thickness=thickness)


def draw_smiley(frame: ndarray, position: tuple[int, int], smiley: str):
    # Create an image with RGBA (to support transparency)
    emoji_size = 65
    emoji_image = Image.new("RGBA", (emoji_size, emoji_size), (0, 0, 0, 0))

    # Get a drawing context
    draw = ImageDraw.Draw(emoji_image)

    font_path = "/System/Library/Fonts/Apple Color Emoji.ttc"
    font_size = 64  # Testing, I found that the following sizes work - 20, 32, 40, 48, 64, 96, 160
    font = ImageFont.truetype(font_path, font_size)

    # Draw the emoji
    draw.text((0, 0), smiley, font=font, embedded_color=True)

    # Convert the PIL image to an OpenCV image (in RGBA format)
    emoji_image = np.array(emoji_image)

    # Convert the PIL image to a OpenCV image
    # First, convert to RGB and then to a numpy array
    # Extract the alpha channel from the RGBA emoji image
    alpha_s = emoji_image[:, :, 3] / 255.0
    alpha_l = 1.0 - alpha_s

    # get_emoji position
    x_start, x_end = position[0], position[0] + emoji_size
    y_start, y_end = position[1] - emoji_size, position[1]
    # place emoji underneath the bbox if not enough space above
    if position[1] - emoji_size < 0:
        y_start = position[1]
        y_end = position[1] + emoji_size
    # maybe cannot happen but if too close to the right boundary, shift left
    if position[0] + emoji_size > frame.shape[1]:
        x_start = position[0] - emoji_size
        x_end = position[0]

    # Overlay the emoji on the frame
    for c in range(0, 3):
        frame[y_start:y_end, x_start:x_end, c] = (
                alpha_s * emoji_image[:, :, c] +
                alpha_l * frame[y_start:y_end, x_start:x_end, c]
        )
    return frame


def _calculate_font_scale(text, desired_width, font=cv2.FONT_HERSHEY_SIMPLEX):
    """
    Calculate the font scale for OpenCV's putText function based on the desired width in pixels.

    :param text: The text string to be rendered.
    :param desired_width: The desired width in pixels.
    :param font: The font type.
    :return: The calculated font scale.
    """
    font_scale = 1
    increment = 0.1
    while True:
        textSize = cv2.getTextSize(text, font, font_scale, 1)[0]
        # if textSize[0] < desired_width:
        #     font_scale += increment
        if textSize[0] + 30 > desired_width:
            font_scale -= increment
        else:
            break

        # Break the loop if the increment becomes too small
        if increment < 0.001:
            break

    return font_scale if font_scale > 0 else 0.1
