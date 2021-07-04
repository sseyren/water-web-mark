from enum import Enum
import cv2 as cv
import numpy as np

class WatermarkType(Enum):
    TEXT = "text"
    IMAGE = "image"

class TextPosition(Enum):
    TOP_LEFT = "top_left"
    TOP = "top"
    TOP_RIGHT = "top_right"
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM = "bottom"
    BOTTOM_RIGHT = "bottom_right"

class Color:
    WHITE = (255,255,255)
    BLACK = (0,0,0)

def _find_optimum_scale(img_size:tuple,
                       text:str,
                       font,
                       thickness,
                       size_ratio=0.8,
                       step=0.05,
                       ):
    scale = 0
    text_size = 0, 0
    while all(text_size[i] < (img_size[i] * size_ratio) for i in [0,1]):
        scale += step
        text_size, _ = cv.getTextSize(text, font, scale, thickness)

    return scale

def _get_position(img_size:tuple,
                  box_size:tuple,
                  position=TextPosition.CENTER,
                  ):
    if any(position == p for p in filter(lambda x: "LEFT" in x.name, TextPosition)):
        x = 0
    elif any(position == p for p in filter(lambda x: "_" not in x.name, TextPosition)):
        x = int((img_size[0] - box_size[0]) / 2)
    elif any(position == p for p in filter(lambda x: "RIGHT" in x.name, TextPosition)):
        x = img_size[0] - box_size[0]

    if any(position == p for p in filter(lambda x: "TOP" in x.name, TextPosition)):
        y = box_size[1]
    elif any(position == p for p in filter(lambda x: "CENTER" in x.name, TextPosition)):
        y = int((img_size[1] - box_size[1]) / 2) + box_size[1]
    elif any(position == p for p in filter(lambda x: "BOTTOM" in x.name, TextPosition)):
        y = img_size[1]

    return x, y

def one_text(bstring:bytes,
             text:str,
             position=TextPosition.CENTER,
             size_ratio=0.8,
             alpha=0.5,
             ):
    image = cv.imdecode(np.fromstring(bstring, np.uint8), cv.IMREAD_ANYCOLOR)
    image_height, image_width, _ = image.shape
    image_size = image_width, image_height

    overlay = image.copy()

    font = cv.FONT_HERSHEY_COMPLEX
    #font = cv.FONT_HERSHEY_DUPLEX
    #font = cv.FONT_HERSHEY_PLAIN # *2
    #font = cv.FONT_HERSHEY_SCRIPT_COMPLEX # 1.36
    #font = cv.FONT_HERSHEY_SCRIPT_SIMPLEX # 1.36
    #font = cv.FONT_HERSHEY_SIMPLEX
    #font = cv.FONT_HERSHEY_TRIPLEX
    thickness = 2

    font_size = _find_optimum_scale(image_size, text, font, thickness, size_ratio)

    box_size, baseline = cv.getTextSize(text, font, font_size, thickness)
    box_size = box_size[0], (box_size[1] + baseline)

    pos = _get_position(image_size, box_size, position)
    pos = pos[0], (pos[1] - baseline)

    cv.putText(overlay, text, pos, font, font_size, Color.BLACK, thickness*2, cv.LINE_AA)
    cv.putText(overlay, text, pos, font, font_size, Color.WHITE, thickness, cv.LINE_AA)

    image = cv.addWeighted(overlay, alpha, image, 1 - alpha, 0)
    ret, output = cv.imencode(".png", image)
    return output.tobytes()