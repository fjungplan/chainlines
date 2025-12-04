import pytest
import subprocess
import os
import pathlib
import sys
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.services.lineage_service import LineageService
from app.models.lineage import LineageEvent
from app.models.team import TeamNode
from app.models.enums import EventType
from app.core.config import settings as config


@pytest.mark.asyncio
async def test_add_lineage(tmp_path, monkeypatch):
    # Setup: Create a temporary database and mock the config
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    # Patch the config for the application code under test
    monkeypatch.setattr(config, "DATABASE_URL", db_url)
    # Patch the environment for the alembic subprocess
    monkeypatch.setenv("DATABASE_URL", db_url)

    # Get backend directory - it's the current directory since we're in backend
    backend_dir = pathlib.Path(__file__).parent.parent.parent

    # Run Alembic migrations in a subprocess to avoid event loop conflicts
    # between pytest-asyncio and Alembic's async setup in env.py.
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(backend_dir),
    )

    if result.returncode != 0:
        pytest.fail(
            f"Alembic upgrade failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    # Setup database engine for the test
    engine = create_async_engine(config.DATABASE_URL)

    # Verify that the table was created
    async with engine.connect() as conn:
        has_table = await conn.run_sync(
            lambda sync_conn: sync_conn.dialect.has_table(sync_conn, "lineage_event")
        )
    assert has_table

    # Exercise: Call the service to add lineage data by creating team nodes and event
    async with AsyncSession(engine) as session:
        # Create two team nodes
        node1 = TeamNode(founding_year=2000)
        node2 = TeamNode(founding_year=2010)
        session.add_all([node1, node2])
        await session.flush()
        await session.refresh(node1)
        await session.refresh(node2)
        
        # Create a lineage event
        event = LineageEvent(
            previous_node_id=node1.node_id,
            next_node_id=node2.node_id,
            event_year=2015,
            event_type=EventType.LEGAL_TRANSFER,
            notes="Test transfer"
        )
        session.add(event)
        await session.commit()

        # Verification: Query the database to ensure the data was inserted correctly.
        stmt = select(LineageEvent).where(LineageEvent.event_year == 2015)
        result = await session.execute(stmt)
        saved_event = result.scalar_one_or_none()

        assert saved_event is not None
        assert saved_event.event_type == EventType.LEGAL_TRANSFER
        assert saved_event.notes == "Test transfer"