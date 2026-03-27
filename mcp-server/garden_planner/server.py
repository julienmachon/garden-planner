import os
from datetime import date, datetime
from typing import Optional

from fastmcp import FastMCP

from . import queries
from .db import get_session, init_db
from .models import (
    EndReason,
    EventType,
    MaterialType,
    Quality,
    SourceType,
    StartMethod,
    YieldUnit,
)

mcp = FastMCP("Garden Planner")


def _today() -> date:
    return datetime.now().date()


def _parse_date(d: Optional[str]) -> date:
    return date.fromisoformat(d) if d else _today()


# ---------------------------------------------------------------------------
# Planting Materials
# ---------------------------------------------------------------------------

@mcp.tool()
def add_planting_material(
    name: str,
    material_type: str,
    source_type: str,
    variety: Optional[str] = None,
    species: Optional[str] = None,
    source_detail: Optional[str] = None,
    acquired_at: Optional[str] = None,
    notes: Optional[str] = None,
) -> str:
    """
    Register a new planting material (seed, bulb, tuber, seedling, etc.).

    material_type: seed | bulb | tuber | seedling | cutting | rhizome | bareroot
    source_type:   bought | saved | gift | swap
    acquired_at:   YYYY-MM-DD, defaults to today
    """
    with get_session() as session:
        material = queries.create_material(
            session,
            name=name,
            material_type=MaterialType(material_type),
            source_type=SourceType(source_type),
            variety=variety,
            species=species,
            source_detail=source_detail,
            acquired_at=_parse_date(acquired_at),
            notes=notes,
        )
        return f"Registered '{material.name}' (id={material.id}, type={material_type}, source={source_type})"


@mcp.tool()
def list_planting_materials() -> str:
    """List all registered planting materials."""
    with get_session() as session:
        materials = queries.list_materials(session)
        if not materials:
            return "No planting materials registered yet."
        lines = []
        for m in materials:
            variety = f" ({m.variety})" if m.variety else ""
            lines.append(f"  [{m.id}] {m.name}{variety} — {m.material_type.value}, {m.source_type.value}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Plantings
# ---------------------------------------------------------------------------

@mcp.tool()
def log_planting(
    material_name: str,
    started_location: str,
    start_method: str,
    started_at: Optional[str] = None,
    variety: Optional[str] = None,
    material_type: Optional[str] = None,
    source_type: Optional[str] = None,
    sown_depth_cm: Optional[float] = None,
    notes: Optional[str] = None,
) -> str:
    """
    Log a new planting. Auto-registers the material if it doesn't exist yet.

    start_method:  direct | indoor_start | pot
    started_at:    YYYY-MM-DD, defaults to today
    material_type: seed | bulb | tuber | seedling | cutting | rhizome | bareroot
                   (only needed when auto-registering, defaults to 'seed')
    source_type:   bought | saved | gift | swap
                   (only needed when auto-registering, defaults to 'bought')
    """
    with get_session() as session:
        material = queries.get_material_by_name(session, material_name)
        if not material:
            material = queries.create_material(
                session,
                name=material_name,
                material_type=MaterialType(material_type or "seed"),
                source_type=SourceType(source_type or "bought"),
                variety=variety,
            )
        planting = queries.create_planting(
            session,
            material_id=material.id,
            started_at=_parse_date(started_at),
            started_location=started_location,
            start_method=StartMethod(start_method),
            sown_depth_cm=sown_depth_cm,
            notes=notes,
        )
        return (
            f"Logged planting of '{material_name}' at '{started_location}' "
            f"on {planting.started_at} (planting id={planting.id})"
        )


@mcp.tool()
def log_transplant(
    planting_id: int,
    location: str,
    transplanted_at: Optional[str] = None,
) -> str:
    """
    Record that a plant has been moved to its final outdoor location.

    transplanted_at: YYYY-MM-DD, defaults to today
    """
    with get_session() as session:
        planting = queries.transplant_planting(
            session,
            planting_id=planting_id,
            location=location,
            transplanted_at=_parse_date(transplanted_at),
        )
        return f"Planting {planting_id} transplanted to '{location}' on {planting.transplanted_at}"


@mcp.tool()
def log_event(
    planting_id: int,
    event_type: str,
    occurred_at: Optional[str] = None,
    notes: Optional[str] = None,
) -> str:
    """
    Log a lifecycle event for a planting.

    event_type:  germinated | first_true_leaves | established | first_flower |
                 pollinated | first_fruit_set | pest | disease | pruned | thinned | custom
    occurred_at: YYYY-MM-DD, defaults to today
    """
    with get_session() as session:
        event = queries.create_event(
            session,
            planting_id=planting_id,
            event_type=EventType(event_type),
            occurred_at=_parse_date(occurred_at),
            notes=notes,
        )
        return f"Logged '{event_type}' for planting {planting_id} on {event.occurred_at}"


@mcp.tool()
def log_harvest(
    planting_id: int,
    quantity: float,
    unit: str,
    harvested_at: Optional[str] = None,
    quality: Optional[str] = None,
    notes: Optional[str] = None,
) -> str:
    """
    Record a harvest from a planting.

    unit:         kg | g | count | bunch
    quality:      poor | good | excellent
    harvested_at: YYYY-MM-DD, defaults to today
    """
    with get_session() as session:
        harvest = queries.create_harvest(
            session,
            planting_id=planting_id,
            quantity=quantity,
            unit=YieldUnit(unit),
            harvested_at=_parse_date(harvested_at),
            quality=Quality(quality) if quality else None,
            notes=notes,
        )
        return f"Logged harvest of {quantity} {unit} from planting {planting_id} on {harvest.harvested_at}"


@mcp.tool()
def end_planting(
    planting_id: int,
    end_reason: str,
    ended_at: Optional[str] = None,
    notes: Optional[str] = None,
) -> str:
    """
    Mark a planting as ended.

    end_reason: frost | pulled | died | bolted | overwintered | complete
    ended_at:   YYYY-MM-DD, defaults to today
    """
    with get_session() as session:
        planting = queries.end_planting_record(
            session,
            planting_id=planting_id,
            end_reason=EndReason(end_reason),
            ended_at=_parse_date(ended_at),
            notes=notes,
        )
        return f"Planting {planting_id} ended on {planting.ended_at} (reason: {end_reason})"


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

@mcp.tool()
def get_planting_history(planting_id: int) -> str:
    """Get the complete lifecycle timeline for a planting, seed to harvest."""
    with get_session() as session:
        history = queries.get_planting_history(session, planting_id)
        p = history["planting"]
        m = history["material"]
        events = history["events"]
        harvests = history["harvests"]

        variety = f" ({m.variety})" if m.variety else ""
        source = m.source_detail or m.source_type.value
        lines = [
            f"=== {m.name}{variety} — Planting #{p.id} ===",
            f"Material: {m.material_type.value} from {source}",
            "",
            "Timeline:",
            f"  {p.started_at}  Started ({p.start_method.value}) at '{p.started_location}'"
            + (f" — {p.notes}" if p.notes else ""),
        ]
        if p.transplanted_at:
            lines.append(f"  {p.transplanted_at}  Transplanted to '{p.location}'")

        timeline: list[tuple[date, str]] = []
        for e in events:
            label = f"[event] {e.type.value}" + (f" — {e.notes}" if e.notes else "")
            timeline.append((e.occurred_at, label))
        for h in harvests:
            quality = f", {h.quality.value}" if h.quality else ""
            label = f"[harvest] {h.quantity} {h.unit.value}{quality}" + (f" — {h.notes}" if h.notes else "")
            timeline.append((h.harvested_at, label))

        for dt, label in sorted(timeline):
            lines.append(f"  {dt}  {label}")

        if p.ended_at:
            lines.append(f"  {p.ended_at}  Ended ({p.end_reason.value})")

        if harvests:
            by_unit: dict[str, float] = {}
            for h in harvests:
                by_unit[h.unit.value] = by_unit.get(h.unit.value, 0) + h.quantity
            totals = ", ".join(f"{v} {u}" for u, v in by_unit.items())
            lines.append(f"\nTotal harvested: {totals} across {len(harvests)} harvest(s)")

        return "\n".join(lines)


@mcp.tool()
def list_active_plantings() -> str:
    """List all currently active plantings (not yet ended)."""
    with get_session() as session:
        results = queries.list_active_plantings(session)
        if not results:
            return "No active plantings."
        lines = []
        for planting, material in results:
            location = planting.location or planting.started_location
            variety = f" ({material.variety})" if material.variety else ""
            lines.append(
                f"  [{planting.id}] {material.name}{variety} @ '{location}' since {planting.started_at}"
            )
        return "\n".join(lines)


@mcp.tool()
def get_season_summary(year: Optional[int] = None) -> str:
    """
    Get a summary of all plantings and harvests for a season.
    Defaults to the current year.
    """
    target_year = year or _today().year
    with get_session() as session:
        summary = queries.get_season_summary(session, target_year)
        lines = [
            f"=== {target_year} Season Summary ===",
            f"Plantings: {summary['total_plantings']} total, {summary['active_plantings']} still active",
            f"Harvests:  {summary['total_harvests']} recorded",
            "",
            "Plantings:",
        ]
        for planting, material in summary["plantings"]:
            status = "active" if planting.ended_at is None else planting.end_reason.value
            variety = f" ({material.variety})" if material.variety else ""
            lines.append(f"  [{planting.id}] {material.name}{variety} — {status}")
        return "\n".join(lines)


@mcp.tool()
def search_plantings(
    material_name: Optional[str] = None,
    location: Optional[str] = None,
    active_only: bool = False,
) -> str:
    """Search plantings by plant name or location."""
    with get_session() as session:
        results = queries.search_plantings(session, material_name, location, active_only)
        if not results:
            return "No plantings found."
        lines = []
        for planting, material in results:
            loc = planting.location or planting.started_location
            status = "active" if planting.ended_at is None else planting.end_reason.value
            variety = f" ({material.variety})" if material.variety else ""
            lines.append(f"  [{planting.id}] {material.name}{variety} @ '{loc}' — {status}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    init_db()
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8765"))
    mcp.run(transport="sse", host=host, port=port)


if __name__ == "__main__":
    main()
