import pytest
from sqlalchemy import inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import Base, create_database_engine, session_factory
from app.modules.equipment.models import Equipment


@pytest.fixture
def engine() -> Engine:
    database_engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database_engine)
    return database_engine


@pytest.fixture
def db_session(engine: Engine) -> Session:
    factory = session_factory(engine)
    with factory() as session:
        yield session


def test_equipment_code_is_unique(db_session: Session) -> None:
    db_session.add_all(
        [
            Equipment(code="EQ-001", name="A", organization_id=None),
            Equipment(code="EQ-001", name="B", organization_id=None),
        ]
    )

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_schema_has_no_equipment_grant_table(engine: Engine) -> None:
    assert "equipment_grant" not in inspect(engine).get_table_names()
