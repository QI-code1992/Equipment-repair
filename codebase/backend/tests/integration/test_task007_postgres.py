"""Optional destructive PostgreSQL coverage for TASK-007.

The dedicated environment is supplied by DEV-001; ordinary local runs skip it.
"""

import os
from pathlib import Path

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import create_engine, inspect

from app.modules.agent_runtime.langgraph_runtime import run_checkpoint


POSTGRES_DSN = os.getenv("TASK007_POSTGRES_DSN")
ALLOW_DESTRUCTIVE = os.getenv("TASK007_ALLOW_DESTRUCTIVE_TESTS") == "1"
BACKEND_DIR = Path(__file__).parents[2]
pytestmark = pytest.mark.skipif(
    not POSTGRES_DSN or not ALLOW_DESTRUCTIVE,
    reason="dedicated DSN and TASK007_ALLOW_DESTRUCTIVE_TESTS=1 are required",
)


def test_task007_postgres_migration_round_trip() -> None:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("path_separator", "os")
    engine = create_engine(POSTGRES_DSN)
    previous = os.environ.get("POSTGRES_DSN")
    os.environ["POSTGRES_DSN"] = POSTGRES_DSN
    try:
        command.upgrade(config, "0005_task007")
        assert {
            "agent_threads", "agent_runs", "agent_tool_calls", "agent_confirmations"
        } <= set(inspect(engine).get_table_names())
        first = run_checkpoint(
            run_id="postgres-checkpoint-test",
            initial_state={"step": "historical", "events": [{"event": "historical", "data": {"value": 7}}]},
            database_url=POSTGRES_DSN,
        )
        resumed = run_checkpoint(
            run_id="postgres-checkpoint-test",
            initial_state={"confirmation": {"approved": True}},
            database_url=POSTGRES_DSN,
            resumed=True,
        )
        assert first["step"] == "waiting_for_model"
        assert any(item["event"] == "historical" for item in resumed["events"])
        assert resumed["confirmation"] == {"approved": True}
        command.downgrade(config, "0004_task006")
        assert not ({"agent_threads", "agent_runs", "agent_tool_calls", "agent_confirmations"} & set(inspect(engine).get_table_names()))
    finally:
        if previous is None:
            os.environ.pop("POSTGRES_DSN", None)
        else:
            os.environ["POSTGRES_DSN"] = previous
        engine.dispose()
