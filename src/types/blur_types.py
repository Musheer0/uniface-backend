from enum import Enum

class BlurMethod(str, Enum):
    PIXELATE = "pixelate"
    GAUSSIAN = "gaussian"
    BLACKOUT = "blackout"
    ELLIPTICAL = "elliptical"
    MEDIAN = "median"