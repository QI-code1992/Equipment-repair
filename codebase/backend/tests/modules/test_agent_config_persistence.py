from dataclasses import replace

import pytest
from sqlalchemy import UniqueConstraint, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import Base, create_database_engine, session_factory
from app.modules.agent_config.domain import AgentConfig, AgentId, DeepThinkingLevel
from app.modules.agent_config.models import AgentConfigModel, ModelBinding, ModelProvider
from app.modules.agent_config.repository import SqlAgentConfigRepository, SqlModelCatalog
from app.modules.agent_config.service import AgentConfigError, AgentConfigService
from app.modules.identity.models import User


@pytest.fixture
def db_session() -> Session:
    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    event.listen(
        engine,
        "connect",
        lambda connection, _: connection.execute("PRAGMA foreign_keys=ON"),
    )
    Base.metadata.create_all(engine)
    factory = session_factory(engine)
    with factory() as session:
        yield session
    Base.metadata.drop_all(engine)


def add_binding(
    db_session: Session,
    *,
    binding_id: str = "reasoning-pro",
    provider_enabled: bool = True,
    binding_enabled: bool = True,
    supports_reasoning: bool = True,
) -> ModelBinding:
    provider = ModelProvider(
        id=f"provider-{binding_id}",
        name=f"Provider {binding_id}",
        secret_ref="vault://models/not-for-response",
        enabled=provider_enabled,
    )
    binding = ModelBinding(
        id=binding_id,
        provider_id=provider.id,
        name=f"Binding {binding_id}",
        model_name="model-v1",
        supports_reasoning=supports_reasoning,
        enabled=binding_enabled,
    )
    db_session.add(provider)
    db_session.flush()
    db_session.add(binding)
    db_session.commit()
    return binding


def test_sql_repository_initializes_only_requested_agent(db_session: Session) -> None:
    repository = SqlAgentConfigRepository(db_session)
    service = AgentConfigService(repository, SqlModelCatalog(db_session))

    created = service.initialize("fault_reporting")

    assert created.agent_id is AgentId.FAULT_REPORTING
    assert repository.list_all() == [created]
    assert db_session.query(AgentConfigModel.agent_id).all() == [
        (AgentId.FAULT_REPORTING.value,)
    ]


def test_orm_models_preserve_named_unique_constraints_from_migration() -> None:
    binding_constraint_names = {
        constraint.name
        for constraint in ModelBinding.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    config_constraint_names = {
        constraint.name
        for constraint in AgentConfigModel.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert "uq_model_bindings_provider_name" in binding_constraint_names
    assert "uq_agent_configs_agent_id" in config_constraint_names


@pytest.mark.parametrize(
    ("model", "column_name", "expected_default"),
    [
        (ModelProvider, "enabled", "true"),
        (ModelBinding, "supports_reasoning", "false"),
        (ModelBinding, "enabled", "true"),
    ],
)
def test_orm_boolean_server_defaults_match_migration(
    model: type[ModelProvider] | type[ModelBinding],
    column_name: str,
    expected_default: str,
) -> None:
    column = model.__table__.c[column_name]

    assert column.server_default is not None
    assert str(column.server_default.arg).lower() == expected_default


def test_sqlite_fixture_enforces_agent_config_model_binding_foreign_key(
    db_session: Session,
) -> None:
    repository = SqlAgentConfigRepository(db_session)
    invalid_config = replace(
        AgentConfig.default_for(AgentId.METRIC_QUERY),
        model_binding_id="missing-binding",
    )

    with pytest.raises(IntegrityError):
        repository.save(invalid_config)
    db_session.rollback()

    assert repository.get(AgentId.METRIC_QUERY) is None

    valid_config = AgentConfig.default_for(AgentId.METRIC_QUERY)
    assert repository.save(valid_config) == valid_config
    assert db_session.in_transaction()
    db_session.commit()

    assert repository.get(AgentId.METRIC_QUERY) == valid_config


def test_sql_repository_returns_committed_config_after_actual_unique_race(
    tmp_path,
) -> None:
    engine = create_database_engine(f"sqlite+pysqlite:///{tmp_path / 'agent-config-race.db'}")
    event.listen(
        engine,
        "connect",
        lambda connection, _: connection.execute("PRAGMA foreign_keys=ON"),
    )
    Base.metadata.create_all(engine)
    factory = session_factory(engine)
    agent_id = AgentId.FAULT_REPORTING
    first_result: list[AgentConfig] = []
    first_initialized = False
    unique_conflict_seen = False

    def initialize_first_session_before_second_insert(
        connection, cursor, statement, parameters, context, executemany
    ) -> None:
        nonlocal first_initialized
        if first_initialized or "INSERT INTO agent_configs" not in statement:
            return

        first_initialized = True
        with factory() as first_session:
            first_service = AgentConfigService(
                SqlAgentConfigRepository(first_session), SqlModelCatalog(first_session)
            )
            first_result.append(first_service.initialize(agent_id))
            first_session.commit()

    def record_unique_conflict(exception_context) -> None:
        nonlocal unique_conflict_seen
        if (
            exception_context.statement
            and "INSERT INTO agent_configs" in exception_context.statement
            and "UNIQUE constraint failed: agent_configs.agent_id"
            in str(exception_context.original_exception)
        ):
            unique_conflict_seen = True

    event.listen(engine, "before_cursor_execute", initialize_first_session_before_second_insert)
    event.listen(engine, "handle_error", record_unique_conflict)
    try:
        with factory() as second_session:
            second_repository = SqlAgentConfigRepository(second_session)
            second_service = AgentConfigService(
                second_repository, SqlModelCatalog(second_session)
            )

            assert second_repository.get(agent_id) is None
            second_result = second_service.initialize(agent_id)

            assert first_initialized
            assert unique_conflict_seen
            assert second_result == first_result[0]
            assert second_repository.list_all() == [first_result[0]]

        with factory() as verification_session:
            assert SqlAgentConfigRepository(verification_session).list_all() == [
                first_result[0]
            ]
    finally:
        event.remove(engine, "before_cursor_execute", initialize_first_session_before_second_insert)
        event.remove(engine, "handle_error", record_unique_conflict)
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.mark.parametrize("provider_enabled,binding_enabled", [(False, True), (True, False)])
def test_disabled_provider_or_binding_is_not_returned_or_accepted(
    db_session: Session, provider_enabled: bool, binding_enabled: bool
) -> None:
    binding = add_binding(
        db_session,
        provider_enabled=provider_enabled,
        binding_enabled=binding_enabled,
    )
    catalog = SqlModelCatalog(db_session)
    service = AgentConfigService(SqlAgentConfigRepository(db_session), catalog)
    candidate = replace(
        AgentConfig.default_for(AgentId.METRIC_QUERY),
        enabled=True,
        model_binding_id=binding.id,
    )

    assert catalog.get(binding.id) is None
    with pytest.raises(AgentConfigError, match="模型绑定不存在"):
        service.save("metric_query", candidate)


def test_deep_thinking_requires_reasoning_binding(db_session: Session) -> None:
    binding = add_binding(db_session, supports_reasoning=False)
    service = AgentConfigService(
        SqlAgentConfigRepository(db_session), SqlModelCatalog(db_session)
    )
    candidate = replace(
        AgentConfig.default_for(AgentId.FAULT_DIAGNOSIS),
        model_binding_id=binding.id,
        deep_thinking_enabled=True,
    )

    with pytest.raises(AgentConfigError, match="当前模型不支持深度思考"):
        service.save("fault_diagnosis", candidate)


def test_sql_repository_round_trips_json_ids_and_all_domain_fields(
    db_session: Session,
) -> None:
    binding = add_binding(db_session)
    repository = SqlAgentConfigRepository(db_session)
    original = AgentConfig(
        agent_id=AgentId.OPERATION_GUIDANCE,
        enabled=True,
        model_binding_id=binding.id,
        knowledge_dataset_ids=("dataset-a", "dataset-b"),
        streaming_enabled=False,
        suggestions_enabled=False,
        sources_enabled=False,
        context_turns=8,
        retrieval_limit=12,
        similarity_threshold=0.87,
        deep_thinking_enabled=True,
        deep_thinking_level=DeepThinkingLevel.HIGH,
        max_reply_tokens=8192,
    )

    saved = repository.save(original)
    db_session.flush()

    assert saved == original
    assert repository.get(AgentId.OPERATION_GUIDANCE) == original
    assert db_session.get(AgentConfigModel, db_session.query(AgentConfigModel.id).scalar()).knowledge_dataset_ids == [
        "dataset-a",
        "dataset-b",
    ]
