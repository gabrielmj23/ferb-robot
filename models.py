from pydantic import BaseModel
from typing import Literal


class MoveRequest(BaseModel):
    """Representa una solicitud de movimiento del robot."""

    direction: Literal["forward", "backward", "left", "right", "stop"] = "stop"


class ModeRequest(BaseModel):
    """Representa una solicitud de cambio de modo del robot."""

    mode: Literal["manual", "dog"] = "manual"
