"""
Unit tests for garden_planner queries.
Uses an in-memory SQLite database — no file I/O.
"""
import pytest
from datetime import date
from sqlmodel import SQLModel, Session, create_engine

from garden_planner import queries
from garden_planner.models import (
    MaterialType,
    SourceType,
    StartMethod,
    EndReason,
    EventType,
    YieldUnit,
    Quality,
)


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def tomato(session):
    return queries.create_material(
        session,
        name="Tomato",
        material_type=MaterialType.seed,
        source_type=SourceType.bought,
        variety="Cherry",
    )


@pytest.fixture
def tomato_planting(session, tomato):
    return queries.create_planting(
        session,
        material_id=tomato.id,
        started_at=date(2026, 3, 1),
        started_location="Seed tray A",
        start_method=StartMethod.indoor_start,
    )


# ---------------------------------------------------------------------------
# Planting materials
# ---------------------------------------------------------------------------

class TestPlantingMaterials:
    def test_create_material(self, session):
        m = queries.create_material(
            session,
            name="Carrot",
            material_type=MaterialType.seed,
            source_type=SourceType.bought,
            variety="Nantes",
        )
        assert m.id is not None
        assert m.name == "Carrot"
        assert m.variety == "Nantes"
        assert m.material_type == MaterialType.seed

    def test_get_material_by_name(self, session, tomato):
        found = queries.get_material_by_name(session, "Tomato")
        assert found is not None
        assert found.id == tomato.id

    def test_get_material_by_name_not_found(self, session):
        assert queries.get_material_by_name(session, "Nonexistent") is None

    def test_list_materials(self, session, tomato):
        queries.create_material(
            session, name="Carrot", material_type=MaterialType.seed, source_type=SourceType.bought
        )
        materials = queries.list_materials(session)
        assert len(materials) == 2
        names = [m.name for m in materials]
        assert "Tomato" in names
        assert "Carrot" in names

    def test_material_types(self, session):
        for mat_type in [MaterialType.bulb, MaterialType.tuber, MaterialType.seedling]:
            m = queries.create_material(
                session,
                name=f"Plant_{mat_type.value}",
                material_type=mat_type,
                source_type=SourceType.bought,
            )
            assert m.material_type == mat_type


# ---------------------------------------------------------------------------
# Plantings
# ---------------------------------------------------------------------------

class TestPlantings:
    def test_create_planting(self, session, tomato):
        p = queries.create_planting(
            session,
            material_id=tomato.id,
            started_at=date(2026, 3, 1),
            started_location="Seed tray A",
            start_method=StartMethod.indoor_start,
        )
        assert p.id is not None
        assert p.material_id == tomato.id
        assert p.started_at == date(2026, 3, 1)
        assert p.ended_at is None

    def test_transplant_planting(self, session, tomato_planting):
        p = queries.transplant_planting(
            session,
            planting_id=tomato_planting.id,
            location="Bed 3",
            transplanted_at=date(2026, 4, 15),
        )
        assert p.location == "Bed 3"
        assert p.transplanted_at == date(2026, 4, 15)

    def test_transplant_unknown_planting(self, session):
        with pytest.raises(ValueError, match="not found"):
            queries.transplant_planting(session, planting_id=999, location="Bed 1", transplanted_at=date.today())

    def test_end_planting(self, session, tomato_planting):
        p = queries.end_planting_record(
            session,
            planting_id=tomato_planting.id,
            end_reason=EndReason.frost,
            ended_at=date(2026, 10, 1),
        )
        assert p.ended_at == date(2026, 10, 1)
        assert p.end_reason == EndReason.frost

    def test_end_unknown_planting(self, session):
        with pytest.raises(ValueError, match="not found"):
            queries.end_planting_record(session, planting_id=999, end_reason=EndReason.frost, ended_at=date.today())

    def test_list_active_plantings(self, session, tomato, tomato_planting):
        # Add a second planting and end it
        p2 = queries.create_planting(
            session,
            material_id=tomato.id,
            started_at=date(2026, 3, 5),
            started_location="Bed 2",
            start_method=StartMethod.direct,
        )
        queries.end_planting_record(
            session, planting_id=p2.id, end_reason=EndReason.died, ended_at=date(2026, 4, 1)
        )
        active = queries.list_active_plantings(session)
        assert len(active) == 1
        assert active[0][0].id == tomato_planting.id

    def test_search_by_name(self, session, tomato, tomato_planting):
        results = queries.search_plantings(session, material_name="Tomato")
        assert len(results) == 1

        results = queries.search_plantings(session, material_name="omato")  # partial
        assert len(results) == 1

        results = queries.search_plantings(session, material_name="Carrot")
        assert len(results) == 0

    def test_search_active_only(self, session, tomato, tomato_planting):
        p2 = queries.create_planting(
            session,
            material_id=tomato.id,
            started_at=date(2026, 3, 5),
            started_location="Bed 2",
            start_method=StartMethod.direct,
        )
        queries.end_planting_record(
            session, planting_id=p2.id, end_reason=EndReason.died, ended_at=date(2026, 4, 1)
        )
        results = queries.search_plantings(session, active_only=True)
        assert all(p.ended_at is None for p, _ in results)


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

class TestEvents:
    def test_create_event(self, session, tomato_planting):
        e = queries.create_event(
            session,
            planting_id=tomato_planting.id,
            event_type=EventType.germinated,
            occurred_at=date(2026, 3, 10),
        )
        assert e.id is not None
        assert e.type == EventType.germinated

    def test_create_event_unknown_planting(self, session):
        with pytest.raises(ValueError, match="not found"):
            queries.create_event(
                session, planting_id=999, event_type=EventType.germinated, occurred_at=date.today()
            )

    def test_events_ordered_by_date(self, session, tomato_planting):
        queries.create_event(session, planting_id=tomato_planting.id, event_type=EventType.first_flower, occurred_at=date(2026, 5, 20))
        queries.create_event(session, planting_id=tomato_planting.id, event_type=EventType.germinated, occurred_at=date(2026, 3, 10))
        queries.create_event(session, planting_id=tomato_planting.id, event_type=EventType.established, occurred_at=date(2026, 4, 1))

        events = queries.get_events_for_planting(session, tomato_planting.id)
        dates = [e.occurred_at for e in events]
        assert dates == sorted(dates)


# ---------------------------------------------------------------------------
# Harvests
# ---------------------------------------------------------------------------

class TestHarvests:
    def test_create_harvest(self, session, tomato_planting):
        h = queries.create_harvest(
            session,
            planting_id=tomato_planting.id,
            quantity=1.5,
            unit=YieldUnit.kg,
            harvested_at=date(2026, 7, 10),
            quality=Quality.good,
        )
        assert h.id is not None
        assert h.quantity == 1.5
        assert h.unit == YieldUnit.kg
        assert h.quality == Quality.good

    def test_create_harvest_unknown_planting(self, session):
        with pytest.raises(ValueError, match="not found"):
            queries.create_harvest(
                session, planting_id=999, quantity=1.0, unit=YieldUnit.kg, harvested_at=date.today()
            )

    def test_multiple_harvests(self, session, tomato_planting):
        queries.create_harvest(session, planting_id=tomato_planting.id, quantity=0.5, unit=YieldUnit.kg, harvested_at=date(2026, 7, 1))
        queries.create_harvest(session, planting_id=tomato_planting.id, quantity=1.2, unit=YieldUnit.kg, harvested_at=date(2026, 7, 15))
        queries.create_harvest(session, planting_id=tomato_planting.id, quantity=0.8, unit=YieldUnit.kg, harvested_at=date(2026, 8, 1))

        harvests = queries.get_harvests_for_planting(session, tomato_planting.id)
        assert len(harvests) == 3
        total = sum(h.quantity for h in harvests)
        assert total == pytest.approx(2.5)


# ---------------------------------------------------------------------------
# Full lifecycle
# ---------------------------------------------------------------------------

class TestLifecycle:
    def test_seed_to_harvest(self, session):
        # Register seed
        material = queries.create_material(
            session,
            name="Zucchini",
            material_type=MaterialType.seed,
            source_type=SourceType.saved,
            variety="Black Beauty",
        )

        # Sow indoors
        planting = queries.create_planting(
            session,
            material_id=material.id,
            started_at=date(2026, 4, 1),
            started_location="Seed tray B",
            start_method=StartMethod.indoor_start,
        )

        # Germination
        queries.create_event(session, planting_id=planting.id, event_type=EventType.germinated, occurred_at=date(2026, 4, 8))

        # Transplant outdoors
        queries.transplant_planting(session, planting_id=planting.id, location="Bed 2", transplanted_at=date(2026, 5, 10))

        # First flower
        queries.create_event(session, planting_id=planting.id, event_type=EventType.first_flower, occurred_at=date(2026, 6, 5))

        # Harvests
        queries.create_harvest(session, planting_id=planting.id, quantity=3, unit=YieldUnit.count, harvested_at=date(2026, 7, 1))
        queries.create_harvest(session, planting_id=planting.id, quantity=5, unit=YieldUnit.count, harvested_at=date(2026, 7, 10))

        # End of season
        queries.end_planting_record(session, planting_id=planting.id, end_reason=EndReason.frost, ended_at=date(2026, 10, 15))

        # Verify full history
        history = queries.get_planting_history(session, planting.id)
        assert history["material"].name == "Zucchini"
        assert len(history["events"]) == 2
        assert len(history["harvests"]) == 2
        assert history["planting"].ended_at == date(2026, 10, 15)
        assert sum(h.quantity for h in history["harvests"]) == 8

    def test_season_summary(self, session):
        m = queries.create_material(session, name="Lettuce", material_type=MaterialType.seed, source_type=SourceType.bought)

        p1 = queries.create_planting(session, material_id=m.id, started_at=date(2026, 3, 1), started_location="Bed 1", start_method=StartMethod.direct)
        p2 = queries.create_planting(session, material_id=m.id, started_at=date(2026, 3, 15), started_location="Bed 2", start_method=StartMethod.direct)

        queries.create_harvest(session, planting_id=p1.id, quantity=2, unit=YieldUnit.bunch, harvested_at=date(2026, 5, 1))
        queries.end_planting_record(session, planting_id=p1.id, end_reason=EndReason.complete, ended_at=date(2026, 5, 1))

        summary = queries.get_season_summary(session, 2026)
        assert summary["total_plantings"] == 2
        assert summary["active_plantings"] == 1
        assert summary["total_harvests"] == 1
