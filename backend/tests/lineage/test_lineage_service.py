import pytest
import subprocess
import os
import pathlib
import sys
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from src.lineage.service import LineageService
from src.lineage.schemas import LineageCreate
from src.models.lineage import Lineage
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

    # The project root is where pytest.ini is. Pytest provides this via the config.
    project_root = pathlib.Path(monkeypatch.config.rootpath)
    backend_dir = project_root / "backend"

    # Run Alembic migrations in a subprocess to avoid event loop conflicts
    # between pytest-asyncio and Alembic's async setup in env.py.
    # We set the subprocess's working directory to `backend` so it can find `alembic.ini`.
    # The `prepend_sys_path = .` in alembic.ini will then correctly add the `backend`
    # directory to the Python path, allowing it to find the `src` module.
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

        # Verification: Query the database to ensure the data was inserted correctly.
        stmt = select(Lineage).where(Lineage.source_table == "source")
        result = await session.execute(stmt)
        saved_lineage = result.scalar_one_or_none()

        assert saved_lineage is not None
        assert saved_lineage.target_table == "target"
        assert saved_lineage.source_columns == ["a", "b"]
        assert saved_lineage.transformation == "SELECT a, b FROM source"