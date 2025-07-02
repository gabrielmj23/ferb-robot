from pydantic import BaseModel
from typing import Literal


class MoveRequest(BaseModel):
    """Representa una solicitud de movimiento del robot."""

    direction: Literal["forward", "backward", "left", "right", "stop"] = "stop"
    speed: float = 1.0


class ModeRequest(BaseModel):
    """Representa una solicitud de cambio de modo del robot."""

    mode: Literal["manual", "dog", "navegacion", "gestos"] = "manual"


class Coordenada(BaseModel):
    """Representa una coordenada GPS."""

    lat: float
    lng: float


class NavigationRequest(BaseModel):
    """Representa una solicitud de navegación."""

    ruta: list[Coordenada] = []  # Lista de coordenadas GPS que forman la ruta
