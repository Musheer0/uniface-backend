from enum import Enum
from typing import Annotated

from pydantic import Field

class BlurMethod(str, Enum):
    PIXELATE = "pixelate"
    GAUSSIAN = "gaussian"
    BLACKOUT = "blackout"
    ELLIPTICAL = "elliptical"
    MEDIAN = "median"


# A [start, end] range in seconds (inclusive on both ends).
# Shared here (types layer) so both schemas/ and lib/ can import it
# without a layer inversion.
TimestampRange = Annotated[
    tuple[Annotated[float, Field(ge=0)], Annotated[float, Field(ge=0)]],
    Field(min_length=2, max_length=2),
]
TimestampRanges = list[TimestampRange]