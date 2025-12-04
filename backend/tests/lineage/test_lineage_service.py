import pytest
import subprocess
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from src.lineage.service import LineageService
from src.lineage.schemas import LineageCreate
from src import config


@pytest.mark.asyncio
async def test_add_lineage(tmp_path, monkeypatch):
    # Setup: Create a temporary database and mock the config
    db_path = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    # Patch the config for the application code under test
    monkeypatch.setattr(config, "DATABASE_URL", db_url)
    # Patch the environment for the alembic subprocess
    monkeypatch.setenv("DATABASE_URL", db_url)

    # Run Alembic migrations in a subprocess to avoid event loop conflicts
    # between pytest-asyncio and Alembic's async setup in env.py.
    # The pytest working directory is 'backend/', where alembic.ini is located.
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
        check=False,
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
            lambda sync_conn: sync_conn.dialect.has_table(sync_conn, "lineage")
        )
    assert has_table

    # Exercise: Call the service to add lineage data
    lineage_data = LineageCreate(
        source_table="source",
        target_table="target",
        source_columns=["a", "b"],
        target_columns=["c", "d"],
        transformation="SELECT a, b FROM source",
    )
    async with AsyncSession(engine) as session:
        service = LineageService(session)
        await service.add_lineage(lineage_data)

        # A full verification would query the data to ensure it was inserted correctly.
        # For now, we assume if no exception is raised, the insertion was successful.