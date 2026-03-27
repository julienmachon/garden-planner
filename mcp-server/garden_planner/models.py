from datetime import date
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class MaterialType(str, Enum):
    seed = "seed"
    bulb = "bulb"
    tuber = "tuber"
    seedling = "seedling"
    cutting = "cutting"
    rhizome = "rhizome"
    bareroot = "bareroot"


class SourceType(str, Enum):
    bought = "bought"
    saved = "saved"
    gift = "gift"
    swap = "swap"


class StartMethod(str, Enum):
    direct = "direct"
    indoor_start = "indoor_start"
    pot = "pot"


class EndReason(str, Enum):
    frost = "frost"
    pulled = "pulled"
    died = "died"
    bolted = "bolted"
    overwintered = "overwintered"
    complete = "complete"


class EventType(str, Enum):
    germinated = "germinated"
    first_true_leaves = "first_true_leaves"
    established = "established"
    first_flower = "first_flower"
    pollinated = "pollinated"
    first_fruit_set = "first_fruit_set"
    pest = "pest"
    disease = "disease"
    pruned = "pruned"
    thinned = "thinned"
    custom = "custom"


class YieldUnit(str, Enum):
    kg = "kg"
    g = "g"
    count = "count"
    bunch = "bunch"


class Quality(str, Enum):
    poor = "poor"
    good = "good"
    excellent = "excellent"


class PlantingMaterial(SQLModel, table=True):
    __tablename__ = "planting_materials"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    variety: Optional[str] = None
    species: Optional[str] = None
    material_type: MaterialType
    source_type: SourceType
    source_detail: Optional[str] = None
    acquired_at: Optional[date] = None
    notes: Optional[str] = None


class Planting(SQLModel, table=True):
    __tablename__ = "plantings"

    id: Optional[int] = Field(default=None, primary_key=True)
    material_id: int = Field(foreign_key="planting_materials.id")
    started_at: date
    started_location: str
    start_method: StartMethod
    sown_depth_cm: Optional[float] = None
    transplanted_at: Optional[date] = None
    location: Optional[str] = None  # final outdoor location after transplant
    ended_at: Optional[date] = None
    end_reason: Optional[EndReason] = None
    notes: Optional[str] = None


class Event(SQLModel, table=True):
    __tablename__ = "events"

    id: Optional[int] = Field(default=None, primary_key=True)
    planting_id: int = Field(foreign_key="plantings.id")
    type: EventType
    occurred_at: date
    notes: Optional[str] = None


class Harvest(SQLModel, table=True):
    __tablename__ = "harvests"

    id: Optional[int] = Field(default=None, primary_key=True)
    planting_id: int = Field(foreign_key="plantings.id")
    harvested_at: date
    quantity: float
    unit: YieldUnit
    quality: Optional[Quality] = None
    notes: Optional[str] = None
