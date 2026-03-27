from datetime import date
from typing import Optional

from sqlmodel import Session, func, select

from .models import (
    EndReason,
    Event,
    EventType,
    Harvest,
    Planting,
    PlantingMaterial,
    Quality,
    SourceType,
    StartMethod,
    YieldUnit,
    MaterialType,
)


# --- Planting Materials ---

def create_material(
    session: Session,
    name: str,
    material_type: MaterialType,
    source_type: SourceType,
    variety: Optional[str] = None,
    species: Optional[str] = None,
    source_detail: Optional[str] = None,
    acquired_at: Optional[date] = None,
    notes: Optional[str] = None,
) -> PlantingMaterial:
    material = PlantingMaterial(
        name=name,
        material_type=material_type,
        source_type=source_type,
        variety=variety,
        species=species,
        source_detail=source_detail,
        acquired_at=acquired_at,
        notes=notes,
    )
    session.add(material)
    session.commit()
    session.refresh(material)
    return material


def get_material_by_name(session: Session, name: str) -> Optional[PlantingMaterial]:
    return session.exec(
        select(PlantingMaterial).where(PlantingMaterial.name == name)
    ).first()


def list_materials(session: Session) -> list[PlantingMaterial]:
    return list(session.exec(select(PlantingMaterial).order_by(PlantingMaterial.name)).all())


# --- Plantings ---

def create_planting(
    session: Session,
    material_id: int,
    started_at: date,
    started_location: str,
    start_method: StartMethod,
    sown_depth_cm: Optional[float] = None,
    notes: Optional[str] = None,
) -> Planting:
    planting = Planting(
        material_id=material_id,
        started_at=started_at,
        started_location=started_location,
        start_method=start_method,
        sown_depth_cm=sown_depth_cm,
        notes=notes,
    )
    session.add(planting)
    session.commit()
    session.refresh(planting)
    return planting


def get_planting(session: Session, planting_id: int) -> Optional[Planting]:
    return session.get(Planting, planting_id)


def transplant_planting(
    session: Session,
    planting_id: int,
    location: str,
    transplanted_at: date,
) -> Planting:
    planting = session.get(Planting, planting_id)
    if not planting:
        raise ValueError(f"Planting {planting_id} not found")
    planting.location = location
    planting.transplanted_at = transplanted_at
    session.add(planting)
    session.commit()
    session.refresh(planting)
    return planting


def end_planting_record(
    session: Session,
    planting_id: int,
    end_reason: EndReason,
    ended_at: date,
    notes: Optional[str] = None,
) -> Planting:
    planting = session.get(Planting, planting_id)
    if not planting:
        raise ValueError(f"Planting {planting_id} not found")
    planting.ended_at = ended_at
    planting.end_reason = end_reason
    if notes:
        planting.notes = (planting.notes + " | " + notes) if planting.notes else notes
    session.add(planting)
    session.commit()
    session.refresh(planting)
    return planting


def list_active_plantings(session: Session) -> list[tuple[Planting, PlantingMaterial]]:
    return list(session.exec(
        select(Planting, PlantingMaterial)
        .join(PlantingMaterial)
        .where(Planting.ended_at == None)  # noqa: E711
        .order_by(Planting.started_at)
    ).all())


def search_plantings(
    session: Session,
    material_name: Optional[str] = None,
    location: Optional[str] = None,
    active_only: bool = False,
) -> list[tuple[Planting, PlantingMaterial]]:
    query = select(Planting, PlantingMaterial).join(PlantingMaterial)
    if material_name:
        query = query.where(PlantingMaterial.name.ilike(f"%{material_name}%"))
    if location:
        query = query.where(
            (Planting.location.ilike(f"%{location}%"))
            | (Planting.started_location.ilike(f"%{location}%"))
        )
    if active_only:
        query = query.where(Planting.ended_at == None)  # noqa: E711
    return list(session.exec(query.order_by(Planting.started_at)).all())


# --- Events ---

def create_event(
    session: Session,
    planting_id: int,
    event_type: EventType,
    occurred_at: date,
    notes: Optional[str] = None,
) -> Event:
    if not session.get(Planting, planting_id):
        raise ValueError(f"Planting {planting_id} not found")
    event = Event(
        planting_id=planting_id,
        type=event_type,
        occurred_at=occurred_at,
        notes=notes,
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


def get_events_for_planting(session: Session, planting_id: int) -> list[Event]:
    return list(session.exec(
        select(Event)
        .where(Event.planting_id == planting_id)
        .order_by(Event.occurred_at)
    ).all())


# --- Harvests ---

def create_harvest(
    session: Session,
    planting_id: int,
    quantity: float,
    unit: YieldUnit,
    harvested_at: date,
    quality: Optional[Quality] = None,
    notes: Optional[str] = None,
) -> Harvest:
    if not session.get(Planting, planting_id):
        raise ValueError(f"Planting {planting_id} not found")
    harvest = Harvest(
        planting_id=planting_id,
        quantity=quantity,
        unit=unit,
        harvested_at=harvested_at,
        quality=quality,
        notes=notes,
    )
    session.add(harvest)
    session.commit()
    session.refresh(harvest)
    return harvest


def get_harvests_for_planting(session: Session, planting_id: int) -> list[Harvest]:
    return list(session.exec(
        select(Harvest)
        .where(Harvest.planting_id == planting_id)
        .order_by(Harvest.harvested_at)
    ).all())


# --- History & Summary ---

def get_planting_history(session: Session, planting_id: int) -> dict:
    planting = session.get(Planting, planting_id)
    if not planting:
        raise ValueError(f"Planting {planting_id} not found")
    material = session.get(PlantingMaterial, planting.material_id)
    return {
        "planting": planting,
        "material": material,
        "events": get_events_for_planting(session, planting_id),
        "harvests": get_harvests_for_planting(session, planting_id),
    }


def get_season_summary(session: Session, year: int) -> dict:
    plantings = list(session.exec(
        select(Planting, PlantingMaterial)
        .join(PlantingMaterial)
        .where(func.strftime("%Y", Planting.started_at) == str(year))
        .order_by(Planting.started_at)
    ).all())

    planting_ids = [p.id for p, _ in plantings]
    harvests = []
    if planting_ids:
        harvests = list(session.exec(
            select(Harvest).where(Harvest.planting_id.in_(planting_ids))
        ).all())

    return {
        "year": year,
        "total_plantings": len(plantings),
        "active_plantings": sum(1 for p, _ in plantings if p.ended_at is None),
        "plantings": plantings,
        "total_harvests": len(harvests),
        "harvests": harvests,
    }
