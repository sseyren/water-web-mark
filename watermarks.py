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

def _add_alpha_channel(image, value=255):
    height, width, channels = image.shape
    if channels != 4:
        return np.dstack(
            [image, np.ones((height, width), dtype="uint8") * value])
    return image

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

def _get_desired_size(img_size:tuple, box_size:tuple, size_ratio=0.8):
    scale = min((img_size[i] / box_size[i]) * size_ratio for i in [0,1])
    return tuple(int(i * scale) for i in box_size)

def _get_position(img_size:tuple,
                  box_size:tuple,
                  position=TextPosition.CENTER,
                  bottom_left=False,
                  ):
    if any(position == p for p in filter(lambda x: "LEFT" in x.name, TextPosition)):
        x = 0
    elif any(position == p for p in filter(lambda x: "_" not in x.name, TextPosition)):
        x = int((img_size[0] - box_size[0]) / 2)
    elif any(position == p for p in filter(lambda x: "RIGHT" in x.name, TextPosition)):
        x = img_size[0] - box_size[0]

    if any(position == p for p in filter(lambda x: "TOP" in x.name, TextPosition)):
        y = 0
    elif any(position == p for p in filter(lambda x: "CENTER" in x.name, TextPosition)):
        y = int((img_size[1] - box_size[1]) / 2)
    elif any(position == p for p in filter(lambda x: "BOTTOM" in x.name, TextPosition)):
        y = img_size[1] - box_size[1]

    if bottom_left:
        y += box_size[1]

    return x, y

def one_text(bstring:bytes,
             text:str,
             position=TextPosition.CENTER,
             size_ratio=0.8,
             alpha=0.5,
             ):
    image = cv.imdecode(np.fromstring(bstring, np.uint8), cv.IMREAD_UNCHANGED)
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

    pos = _get_position(image_size, box_size, position, bottom_left=True)
    pos = pos[0], (pos[1] - baseline)

    cv.putText(overlay, text, pos, font, font_size, Color.BLACK, thickness*2, cv.LINE_AA)
    cv.putText(overlay, text, pos, font, font_size, Color.WHITE, thickness, cv.LINE_AA)

    image = cv.addWeighted(overlay, alpha, image, 1 - alpha, 0)
    ret, output = cv.imencode(".png", image)
    return output.tobytes()

def one_image(image_bstr:bytes,
              watermark_bstr:bytes,
              position=TextPosition.CENTER,
              size_ratio=0.8,
              alpha=0.5,
              ):
    image = cv.imdecode(np.fromstring(image_bstr, np.uint8), cv.IMREAD_UNCHANGED)
    image_height, image_width, _ = image.shape
    image_size = image_width, image_height
    image = _add_alpha_channel(image)

    wm = cv.imdecode(np.fromstring(watermark_bstr, np.uint8), cv.IMREAD_UNCHANGED)
    wm = cv.resize(wm, _get_desired_size(image_size, (wm.shape[1], wm.shape[0]), size_ratio))
    wm_height, wm_width, _ = wm.shape
    wm_size = wm_width, wm_height
    wm = _add_alpha_channel(wm)

    pos = _get_position(image_size, wm_size, position)
    wm_resize = np.zeros((image_height, image_width, 4), dtype="uint8")
    wm_resize[pos[1]:pos[1]+wm_height, pos[0]:pos[0]+wm_width] = wm

    ret, mask = cv.threshold(wm_resize[:,:,3], 10, 255, cv.THRESH_BINARY)
    mask_inv = cv.bitwise_not(mask)

    overlay_bg = cv.bitwise_and(image, image, mask=mask_inv)
    overlay_fg = cv.bitwise_and(wm_resize, wm_resize, mask=mask)

    overlay = cv.add(overlay_bg, overlay_fg)

    image = cv.addWeighted(overlay, alpha, image, 1 - alpha, 0)
    ret, output = cv.imencode(".png", image)
    return output.tobytes()