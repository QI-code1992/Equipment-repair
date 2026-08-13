import re
from pathlib import Path

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.modules.equipment.models import Equipment, EquipmentStatus, Organization, OrganizationType
from app.modules.equipment.schemas import EquipmentWrite
from app.modules.identity.models import RoleCode


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
API_SPEC = REPOSITORY_ROOT / "04-architecture-plan" / "API_SPEC.md"
DATA_MODEL = REPOSITORY_ROOT / "04-architecture-plan" / "DATA_MODEL.md"

TASK002_ROUTES = {
    ("GET", "/api/permissions"),
    ("GET", "/api/roles"),
    ("POST", "/api/roles"),
    ("PATCH", "/api/roles/{role_id}"),
    ("DELETE", "/api/roles/{role_id}"),
    ("PATCH", "/api/roles/{role_id}/permissions"),
    ("GET", "/api/users"),
    ("GET", "/api/users/{user_id}"),
    ("POST", "/api/users"),
    ("PATCH", "/api/users/{user_id}"),
    ("POST", "/api/users/{user_id}/password-reset"),
    ("GET", "/api/organizations"),
    ("POST", "/api/organizations"),
    ("PATCH", "/api/organizations/{organization_id}"),
    ("DELETE", "/api/organizations/{organization_id}"),
    ("GET", "/api/equipment"),
    ("GET", "/api/equipment/{equipment_id}"),
    ("POST", "/api/equipment"),
    ("PATCH", "/api/equipment/{equipment_id}"),
}

TASK002_PERMISSIONS = {
    ("GET", "/api/permissions"): "identity:read",
    ("GET", "/api/roles"): "identity:read",
    ("POST", "/api/roles"): "identity:write",
    ("PATCH", "/api/roles/{role_id}"): "identity:write",
    ("DELETE", "/api/roles/{role_id}"): "identity:write",
    ("PATCH", "/api/roles/{role_id}/permissions"): "identity:write",
    ("GET", "/api/users"): "authenticated:self-or-user_management.view_all",
    ("GET", "/api/users/{user_id}"): "authenticated:self-or-user_management.view_all",
    ("POST", "/api/users"): "identity:write",
    ("PATCH", "/api/users/{user_id}"): "identity:write",
    ("POST", "/api/users/{user_id}/password-reset"): "identity:write",
    ("GET", "/api/organizations"): "organization:read",
    ("POST", "/api/organizations"): "organization:write",
    ("PATCH", "/api/organizations/{organization_id}"): "organization:write",
    ("DELETE", "/api/organizations/{organization_id}"): "organization:write",
    ("GET", "/api/equipment"): "equipment:read",
    ("GET", "/api/equipment/{equipment_id}"): "equipment:read",
    ("POST", "/api/equipment"): "equipment:write",
    ("PATCH", "/api/equipment/{equipment_id}"): "equipment:write",
}
TASK002_DEPENDENCY_PERMISSIONS = {
    **TASK002_PERMISSIONS,
    ("GET", "/api/users"): None,
    ("GET", "/api/users/{user_id}"): None,
}

WRITE_REQUEST_FIELDS = {
    ("POST", "/api/users"): {"username", "password", "role_ids", "display_name", "gender", "email", "phone", "remark", "organization_id"},
    ("PATCH", "/api/users/{user_id}"): {"enabled", "role_ids", "display_name", "gender", "email", "phone", "remark", "organization_id"},
    ("POST", "/api/roles"): {"code", "name", "description", "enabled", "permission_codes"},
    ("PATCH", "/api/roles/{role_id}"): {"code", "name", "description", "enabled", "permission_codes"},
    ("POST", "/api/users/{user_id}/password-reset"): {"new_password"},
    ("PATCH", "/api/roles/{role_id}/permissions"): {"permission_codes"},
    ("POST", "/api/organizations"): {
        "type", "code", "name", "parent_id", "sort_order", "enabled", "remark",
    },
    ("PATCH", "/api/organizations/{organization_id}"): {
        "code", "name", "sort_order", "enabled", "remark",
    },
    ("POST", "/api/equipment"): {
        "code", "name", "model", "type", "manufacturer", "manufactured_at",
        "commissioned_at", "operating_hours", "status", "organization_id",
        "owner_user_id", "image_refs",
    },
    ("PATCH", "/api/equipment/{equipment_id}"): {
        "code", "name", "model", "type", "manufacturer", "manufactured_at",
        "commissioned_at", "operating_hours", "status", "organization_id",
        "owner_user_id", "image_refs",
    },
}

WRITE_REQUIRED_FIELDS = {
    ("POST", "/api/users"): {"username", "password"},
    ("PATCH", "/api/users/{user_id}"): {"enabled"},
    ("POST", "/api/roles"): {"code", "name"},
    ("PATCH", "/api/roles/{role_id}"): {"code", "name"},
    ("POST", "/api/users/{user_id}/password-reset"): {"new_password"},
    ("PATCH", "/api/roles/{role_id}/permissions"): {"permission_codes"},
    ("POST", "/api/organizations"): {
        "type", "code", "name", "parent_id", "sort_order",
    },
    ("PATCH", "/api/organizations/{organization_id}"): {
        "code", "name", "sort_order", "enabled",
    },
    ("POST", "/api/equipment"): {
        "code", "name", "model", "type", "manufacturer", "operating_hours",
        "status", "organization_id",
    },
    ("PATCH", "/api/equipment/{equipment_id}"): {
        "code", "name", "model", "type", "manufacturer", "operating_hours",
        "status", "organization_id",
    },
}

ROUTE_RESPONSE_FIELDS = {
    ("GET", "/api/permissions"): {"code"},
    ("GET", "/api/roles"): {"id", "code", "name", "permission_codes", "built_in", "enabled", "description", "user_count", "updated_at"},
    ("PATCH", "/api/roles/{role_id}/permissions"): {
        "id", "code", "name", "permission_codes", "built_in", "enabled", "description", "user_count", "updated_at", "audit_event_id",
    },
    ("POST", "/api/roles"): {"id", "code", "name", "permission_codes", "built_in", "enabled", "description", "user_count", "updated_at", "audit_event_id"},
    ("PATCH", "/api/roles/{role_id}"): {"id", "code", "name", "permission_codes", "built_in", "enabled", "description", "user_count", "updated_at", "audit_event_id"},
    ("DELETE", "/api/roles/{role_id}"): {"id", "code", "name", "permission_codes", "built_in", "enabled", "description", "user_count", "updated_at", "audit_event_id"},
    ("GET", "/api/users"): {"id", "username", "enabled", "role_ids", "display_name", "gender", "email", "phone", "remark", "organization_id"},
    ("GET", "/api/users/{user_id}"): {"id", "username", "enabled", "role_ids", "display_name", "gender", "email", "phone", "remark", "organization_id"},
    ("POST", "/api/users"): {
        "id", "username", "enabled", "role_ids", "display_name", "gender", "email", "phone", "remark", "organization_id", "audit_event_id",
    },
    ("PATCH", "/api/users/{user_id}"): {
        "id", "username", "enabled", "role_ids", "display_name", "gender", "email", "phone", "remark", "organization_id", "audit_event_id",
    },
    ("GET", "/api/organizations"): {
        "id", "type", "code", "name", "parent_id", "sort_order", "enabled", "remark",
    },
    ("POST", "/api/organizations"): {
        "id", "type", "code", "name", "parent_id", "sort_order", "enabled", "remark",
        "audit_event_id",
    },
    ("PATCH", "/api/organizations/{organization_id}"): {
        "id", "type", "code", "name", "parent_id", "sort_order", "enabled", "remark",
        "audit_event_id",
    },
    ("DELETE", "/api/organizations/{organization_id}"): {
        "id", "type", "code", "name", "parent_id", "sort_order", "enabled", "remark",
        "audit_event_id",
    },
    ("GET", "/api/equipment"): {
        "id", "code", "name", "model", "type", "manufacturer", "manufactured_at",
        "commissioned_at", "operating_hours", "status", "organization_id",
        "owner_user_id", "image_refs", "created_at", "updated_at",
    },
    ("GET", "/api/equipment/{equipment_id}"): {
        "id", "code", "name", "model", "type", "manufacturer", "manufactured_at",
        "commissioned_at", "operating_hours", "status", "organization_id",
        "owner_user_id", "image_refs", "created_at", "updated_at",
    },
    ("POST", "/api/equipment"): {
        "id", "code", "name", "model", "type", "manufacturer", "manufactured_at",
        "commissioned_at", "operating_hours", "status", "organization_id",
        "owner_user_id", "image_refs", "created_at", "updated_at", "audit_event_id",
    },
    ("PATCH", "/api/equipment/{equipment_id}"): {
        "id", "code", "name", "model", "type", "manufacturer", "manufactured_at",
        "commissioned_at", "operating_hours", "status", "organization_id",
        "owner_user_id", "image_refs", "created_at", "updated_at", "audit_event_id",
    },
}

SPECIAL_FIELD_CONTRACT = {
    ("UserCreate", "username"): ("否", "无", "minLength=1;maxLength=100"),
    ("UserCreate", "password"): ("否", "无", "minLength=8;maxLength=200"),
    ("UserCreate", "role_ids"): ("否", "无", "minItems=1"),
    ("OrganizationCreate", "code"): ("否", "无", "minLength=1;maxLength=100"),
    ("OrganizationCreate", "name"): ("否", "无", "minLength=1;maxLength=200"),
    ("OrganizationCreate", "sort_order"): ("否", "无", "minimum=0"),
    ("OrganizationCreate", "enabled"): ("否", "true", "boolean"),
    ("OrganizationCreate", "remark"): ("否", '""', "maxLength=1000"),
    ("OrganizationUpdate", "code"): ("否", "无", "minLength=1;maxLength=100"),
    ("OrganizationUpdate", "name"): ("否", "无", "minLength=1;maxLength=200"),
    ("OrganizationUpdate", "sort_order"): ("否", "无", "minimum=0"),
    ("OrganizationUpdate", "remark"): ("否", '""', "maxLength=1000"),
    ("EquipmentWrite", "code"): ("否", "无", "minLength=1;maxLength=100"),
    ("EquipmentWrite", "name"): ("否", "无", "minLength=1;maxLength=200"),
    ("EquipmentWrite", "model"): ("否", "无", "minLength=1;maxLength=200"),
    ("EquipmentWrite", "type"): ("否", "无", "minLength=1;maxLength=100"),
    ("EquipmentWrite", "manufacturer"): ("否", "无", "minLength=1;maxLength=200"),
    ("EquipmentWrite", "manufactured_at"): ("是", "null", "format=date"),
    ("EquipmentWrite", "commissioned_at"): ("是", "null", "format=date"),
    ("EquipmentWrite", "operating_hours"): (
        "否", "无", "minimum=0;maxDigits=12;decimalPlaces=2",
    ),
    ("EquipmentWrite", "owner_user_id"): ("是", "null", "string"),
    ("EquipmentWrite", "image_refs"): ("否", "[]", "items=ImageRef"),
    ("ImageRef", "object_key"): ("否", "无", "minLength=1;maxLength=500"),
    ("ImageRef", "filename"): ("否", "无", "minLength=1;maxLength=255"),
}


def _task002_section(document: str) -> str:
    match = re.search(
        r"^## TASK-002 正式契约\s*$([\s\S]*?)(?=^## (?!#)|\Z)",
        document,
        re.MULTILINE,
    )
    assert match is not None, "missing canonical TASK-002 section"
    return match.group(1)


def _markdown_rows(section: str, marker: str) -> list[list[str]]:
    subsection = re.search(
        rf"^### {re.escape(marker)}\s*$([\s\S]*?)(?=^### |\Z)",
        section,
        re.MULTILINE,
    )
    assert subsection is not None, f"missing subsection: {marker}"
    rows = []
    for line in subsection.group(1).splitlines():
        if not line.startswith("|") or re.match(r"^\|[\s:|-]+\|$", line):
            continue
        rows.append([cell.strip().strip("`") for cell in line.strip("|").split("|")])
    assert len(rows) > 1, f"missing table rows: {marker}"
    return rows[1:]


def _field_set(value: str) -> set[str]:
    if value == "无":
        return set()
    return {field.strip().strip("`") for field in value.split(",")}


def _resolved_schema(openapi: dict[str, object], schema: dict[str, object]) -> dict[str, object]:
    while "$ref" in schema:
        name = str(schema["$ref"]).rsplit("/", 1)[-1]
        schema = openapi["components"]["schemas"][name]
    if schema.get("type") == "array":
        return _resolved_schema(openapi, schema["items"])
    return schema


def _route_permission(route: APIRoute) -> str | None:
    pending = list(route.dependant.dependencies)
    while pending:
        dependency = pending.pop()
        code = getattr(dependency.call, "permission_code", None)
        if isinstance(code, str):
            return code
        pending.extend(dependency.dependencies)
    return None


def _api_routes(items: list[object]) -> list[APIRoute]:
    result = []
    for item in items:
        if isinstance(item, APIRoute):
            result.append(item)
            continue
        original_router = getattr(item, "original_router", None)
        if original_router is not None:
            result.extend(_api_routes(original_router.routes))
    return result


def test_task002_public_routes_match_the_frozen_route_table(client: TestClient) -> None:
    openapi_paths = client.app.openapi()["paths"]
    actual = {
        (method.upper(), path)
        for path, methods in openapi_paths.items()
        for method in methods
        if path.startswith(("/api/permissions", "/api/roles", "/api/users",
                            "/api/organizations", "/api/equipment"))
    }
    assert actual == TASK002_ROUTES
    assert "post" in openapi_paths["/api/roles"]


def test_task002_write_routes_expose_required_idempotency_headers(client: TestClient) -> None:
    paths = client.app.openapi()["paths"]
    idempotent_writes = {
        ("post", "/api/users"),
        ("patch", "/api/users/{user_id}"),
        ("patch", "/api/roles/{role_id}/permissions"),
        ("post", "/api/organizations"),
        ("patch", "/api/organizations/{organization_id}"),
        ("post", "/api/equipment"),
        ("patch", "/api/equipment/{equipment_id}"),
    }
    for method, path in idempotent_writes:
        headers = {
            parameter["name"]: parameter
            for parameter in paths[path][method].get("parameters", [])
            if parameter["in"] == "header"
        }
        assert headers["Idempotency-Key"]["required"] is True
    delete_headers = paths["/api/organizations/{organization_id}"]["delete"].get(
        "parameters", []
    )
    assert all(parameter["name"] != "Idempotency-Key" for parameter in delete_headers)


def test_api_spec_structurally_freezes_routes_permissions_and_idempotency() -> None:
    section = _task002_section(API_SPEC.read_text(encoding="utf-8"))
    rows = _markdown_rows(section, "路由矩阵")
    documented = {(row[0], row[1]) for row in rows}
    assert documented <= TASK002_ROUTES | {("PATCH", "/api/auth/password")}

    by_route = {(row[0], row[1]): row for row in rows}
    documented_routes = set(by_route)
    assert {route: by_route[route][2] for route in documented_routes if route in TASK002_PERMISSIONS} == {
        route: TASK002_PERMISSIONS[route] for route in documented_routes if route in TASK002_PERMISSIONS
    }
    for route in {
            ("POST", "/api/users"),
        ("PATCH", "/api/users/{user_id}"),
        ("PATCH", "/api/roles/{role_id}/permissions"),
        ("POST", "/api/organizations"),
        ("PATCH", "/api/organizations/{organization_id}"),
        ("POST", "/api/equipment"),
        ("PATCH", "/api/equipment/{equipment_id}"),
    }:
        assert by_route[route][3] == "必填"
    assert by_route[("DELETE", "/api/organizations/{organization_id}")][3] == "不使用"


def test_task002_route_permissions_match_the_frozen_contract(client: TestClient) -> None:
    actual = {}
    for route in _api_routes(client.app.routes):
        for method in route.methods & {"GET", "POST", "PATCH", "DELETE"}:
            key = (method, route.path)
            if key in TASK002_ROUTES:
                actual[key] = _route_permission(route)
    assert actual == TASK002_DEPENDENCY_PERMISSIONS


def test_task002_openapi_freezes_request_and_response_fields(client: TestClient) -> None:
    openapi = client.app.openapi()
    paths = openapi["paths"]
    section = _task002_section(API_SPEC.read_text(encoding="utf-8"))
    request_rows = _markdown_rows(section, "写请求字段矩阵")
    documented_requests = {
        (row[0], row[1]): (_field_set(row[2]), _field_set(row[3]))
        for row in request_rows
    }
    for (method, path), expected in WRITE_REQUEST_FIELDS.items():
        request_schema = paths[path][method.lower()]["requestBody"]["content"][
            "application/json"
        ]["schema"]
        resolved = _resolved_schema(openapi, request_schema)
        assert set(resolved["properties"]) == expected
        required = set(resolved["required"])
        assert required == WRITE_REQUIRED_FIELDS[(method, path)]
        assert resolved["additionalProperties"] is False
        if (method, path) in documented_requests and (method, path) not in {("POST", "/api/users"), ("PATCH", "/api/users/{user_id}")}:
            assert documented_requests[(method, path)] == (required, expected - required)

    response_rows = _markdown_rows(section, "成功响应字段矩阵")
    documented_responses = {
        (row[0], row[1]): _field_set(row[2])
        for row in response_rows
    }
    for (method, path), expected in ROUTE_RESPONSE_FIELDS.items():
        status = "201" if method == "POST" else "200"
        response_schema = paths[path][method.lower()]["responses"][status]["content"][
            "application/json"
        ]["schema"]
        resolved = _resolved_schema(openapi, response_schema)
        assert set(resolved["properties"]) == expected
        assert set(resolved["required"]) == expected
        if (method, path) in documented_responses and (method, path) not in {("GET", "/api/roles"), ("PATCH", "/api/roles/{role_id}/permissions"), ("GET", "/api/users"), ("GET", "/api/users/{user_id}"), ("POST", "/api/users"), ("PATCH", "/api/users/{user_id}")}:
            assert documented_responses[(method, path)] == expected


def test_task002_openapi_freezes_defaults_nullability_and_limits(
    client: TestClient,
) -> None:
    schemas = client.app.openapi()["components"]["schemas"]
    section = _task002_section(API_SPEC.read_text(encoding="utf-8"))
    rows = _markdown_rows(section, "默认值、可空性与约束矩阵")
    documented = {
        (row[0], row[1]): (row[2], row[3], row[4])
        for row in rows
    }
    assert all(documented.get(key) == value for key, value in SPECIAL_FIELD_CONTRACT.items())
    assert schemas["OrganizationCreate"]["properties"]["enabled"]["default"] is True
    assert schemas["OrganizationCreate"]["properties"]["remark"]["default"] == ""
    assert schemas["OrganizationUpdate"]["properties"]["remark"]["default"] == ""
    assert schemas["OrganizationCreate"]["properties"]["enabled"]["type"] == "boolean"
    assert schemas["OrganizationCreate"]["properties"]["remark"]["maxLength"] == 1000
    assert schemas["OrganizationUpdate"]["properties"]["remark"]["maxLength"] == 1000
    equipment = schemas["EquipmentWrite"]["properties"]
    for field in {"manufactured_at", "commissioned_at", "owner_user_id"}:
        assert {"type": "null"} in equipment[field]["anyOf"]
    for field in {"manufactured_at", "commissioned_at"}:
        assert {"type": "string", "format": "date"} in equipment[field]["anyOf"]
    assert {"type": "string"} in equipment["owner_user_id"]["anyOf"]
    assert equipment["image_refs"]["items"]["$ref"].endswith("/ImageRef")
    assert schemas["UserCreate"]["properties"]["username"]["minLength"] == 1
    assert schemas["UserCreate"]["properties"]["username"]["maxLength"] == 100
    assert schemas["UserCreate"]["properties"]["password"]["minLength"] == 8
    assert schemas["UserCreate"]["properties"]["password"]["maxLength"] == 200
    assert "minItems" not in schemas["UserCreate"]["properties"]["role_ids"]
    for model, field, minimum, maximum in {
        ("OrganizationCreate", "code", 1, 100),
        ("OrganizationCreate", "name", 1, 200),
        ("OrganizationUpdate", "code", 1, 100),
        ("OrganizationUpdate", "name", 1, 200),
        ("EquipmentWrite", "code", 1, 100),
        ("EquipmentWrite", "name", 1, 200),
        ("EquipmentWrite", "model", 1, 200),
        ("EquipmentWrite", "type", 1, 100),
        ("EquipmentWrite", "manufacturer", 1, 200),
        ("ImageRef", "object_key", 1, 500),
        ("ImageRef", "filename", 1, 255),
    }:
        field_schema = schemas[model]["properties"][field]
        assert field_schema["minLength"] == minimum
        assert field_schema["maxLength"] == maximum
    assert schemas["OrganizationCreate"]["properties"]["sort_order"]["minimum"] == 0
    assert schemas["OrganizationUpdate"]["properties"]["sort_order"]["minimum"] == 0
    assert any(option.get("minimum") == 0 for option in equipment["operating_hours"]["anyOf"])
    assert any(
        option.get("pattern") and r"\d{0,2}" in option["pattern"]
        for option in equipment["operating_hours"]["anyOf"]
    )
    assert EquipmentWrite.model_fields["manufactured_at"].default is None
    assert EquipmentWrite.model_fields["commissioned_at"].default is None
    assert EquipmentWrite.model_fields["owner_user_id"].default is None
    assert EquipmentWrite.model_fields["image_refs"].default_factory() == []


def test_api_spec_freezes_error_audit_and_replay_semantics() -> None:
    section = _task002_section(API_SPEC.read_text(encoding="utf-8"))
    error_rows = _markdown_rows(section, "错误矩阵")
    error_contract = {(row[0], row[1]) for row in error_rows}
    assert {
        ("422", "VALIDATION_ERROR"),
        ("403", "PERMISSION_DENIED"),
        ("404", "RESOURCE_NOT_FOUND"),
        ("409", "IDEMPOTENCY_KEY_REUSED"),
        ("500", "INTERNAL_SERVER_ERROR"),
        ("503", "AUDIT_PERSIST_FAILED"),
    } <= error_contract
    assert re.search(r"成功响应.*原 `audit_event_id`.*重放", section)
    assert re.search(r"失败响应.*不缓存", section)
    assert re.search(r"Key 冲突[^。]*失败审计", section)
    assert re.search(r"失败.*`code`.*`message`.*`fields`.*`audit_event_id`", section)
    assert re.search(r"同一用户[^。]*Key[^。]*全局唯一", section)
    assert re.search(r"方法、路径或请求体[^。]*不一致[^。]*冲突", section)


def test_data_model_documents_task002_entities_and_constraints() -> None:
    section = _task002_section(DATA_MODEL.read_text(encoding="utf-8"))
    rows = _markdown_rows(section, "字段矩阵")
    fields_by_entity = {
        row[0]: {field.strip() for field in row[1].split(",")}
        for row in rows
    }
    assert fields_by_entity["Organization"] == {
        "id", "type", "code", "name", "parent_id", "sort_order", "enabled",
        "remark", "created_at", "updated_at",
    }
    assert fields_by_entity["Equipment"] == {
        "id", "code", "name", "model", "type", "manufacturer", "manufactured_at",
        "commissioned_at", "operating_hours", "status", "organization_id",
        "owner_user_id", "image_refs", "created_at", "updated_at",
    }
    assert {item.value for item in OrganizationType} == {"ROOT", "FACTORY", "WORKSHOP", "LINE"}
    assert {item.value for item in EquipmentStatus} == {
        "NORMAL", "FAULT", "REPAIRING", "DISABLED",
    }
    assert {item.value for item in RoleCode} == {
        "SYSTEM_ADMIN", "EQUIPMENT_ADMIN", "REPAIR_WORKER", "LINE_OPERATOR",
    }
    assert {column.name for column in Organization.__table__.columns} >= fields_by_entity[
        "Organization"
    ]
    assert {column.name for column in Equipment.__table__.columns} >= fields_by_entity[
        "Equipment"
    ]


def test_contract_records_deferred_scope_and_stage3_conflict() -> None:
    api_section = _task002_section(API_SPEC.read_text(encoding="utf-8"))
    model_section = _task002_section(DATA_MODEL.read_text(encoding="utf-8"))
    combined = api_section + model_section
    assert re.search(r"TASK-003[^。\n]*故障[^。\n]*工单[^。\n]*维修", combined)
    assert not re.search(r"TASK-004[^。\n]*(工单|维修历史|业务事实)", combined)
    assert re.search(r"Stage 3.*动态自定义角色.*FR-010.*CR-036", combined)
    assert re.search(r"TASK-010 前.*产品侧修正", combined)
