from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field

# Each class represents a collection (lowercased name) as per conventions

Status = Literal["prospection", "etude", "travaux", "livre"]
Typologie = Literal[
    "logement",
    "tertiaire",
    "equipement",
    "infrastructure",
]


class Project(BaseModel):
    name: str
    status: Status
    typologie: Typologie
    budget: float = Field(ge=0)
    description: Optional[str] = None
    # GeoJSON Point
    location: dict = Field(..., description="GeoJSON Point {type: 'Point', coordinates: [lon, lat]}")
    # Actors
    maitrise_ouvrage: Optional[str] = None
    architecte: Optional[str] = None
    entreprise: Optional[str] = None
    # Dates (ISO strings)
    date_debut: Optional[str] = None
    date_livraison: Optional[str] = None
