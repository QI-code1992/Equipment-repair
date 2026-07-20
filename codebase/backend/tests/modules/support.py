from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import Base
from app.main import create_app
from app.modules.equipment.models import Organization, OrganizationType
from app.modules.identity.models import Permission, Role, User
from app.modules.identity.security import hash_password


def build_client() -> TestClient:
    app = create_app(
        postgres_dsn="sqlite+pysqlite:///:memory:",
        redis_url="redis://redis:6379/0",
    )
    Base.metadata.create_all(app.state.engine)
    with app.state.session_factory() as db:
        db.add(
            Organization(
                type=OrganizationType.ROOT,
                code="ROOT",
                name="根节点",
                parent_id=None,
                sort_order=0,
                enabled=True,
                remark="",
            )
        )
        db.commit()
    return TestClient(app)


def create_user_token(
    client: TestClient,
    *,
    username: str,
    role_code: str,
    permission_codes: list[str],
) -> tuple[str, str]:
    with client.app.state.session_factory() as db:
        permissions = []
        for code in permission_codes:
            permission = db.scalar(select(Permission).where(Permission.code == code))
            if permission is None:
                permission = Permission(code=code)
                db.add(permission)
            permissions.append(permission)
        role = db.scalar(select(Role).where(Role.code == role_code))
        if role is None:
            role = Role(code=role_code, name=role_code, built_in=True)
            db.add(role)
        role.permissions = permissions
        user = User(username=username, password_hash=hash_password("correct-password"), roles=[role])
        db.add(user)
        db.commit()
        user_id = user.id
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "correct-password"},
    )
    assert response.status_code == 200
    return user_id, response.json()["access_token"]


def valid_equipment_body(
    client: TestClient, *, code: str, name: str = "Loader"
) -> dict[str, object]:
    suffix = uuid4().hex[:8]
    with client.app.state.session_factory() as db:
        root = db.scalar(
            select(Organization).where(Organization.type == OrganizationType.ROOT)
        )
        assert root is not None
        factory = Organization(
            type=OrganizationType.FACTORY,
            code=f"FAC-{suffix}",
            name=f"Factory {suffix}",
            parent_id=root.id,
        )
        workshop = Organization(
            type=OrganizationType.WORKSHOP,
            code=f"WS-{suffix}",
            name=f"Workshop {suffix}",
            parent_id=factory.id,
        )
        line = Organization(
            type=OrganizationType.LINE,
            code=f"LINE-{suffix}",
            name=f"Line {suffix}",
            parent_id=workshop.id,
        )
        owner = User(
            username=f"owner-{suffix}",
            password_hash=hash_password("owner-password"),
            enabled=True,
        )
        db.add_all([factory, workshop, line, owner])
        db.commit()
        line_id = line.id
        owner_id = owner.id
    return {
        "code": code,
        "name": name,
        "model": "MODEL-1",
        "type": "LOADER",
        "manufacturer": "Example",
        "manufactured_at": "2026-01-10",
        "commissioned_at": "2026-02-01",
        "operating_hours": 0,
        "status": "NORMAL",
        "organization_id": line_id,
        "owner_user_id": owner_id,
        "image_refs": [],
    }
