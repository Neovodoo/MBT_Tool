import yaml
import pytest
from MBT_tool_new.test_generator.generator.parser import _is_http_method, extract_paths, _merge_parameters, _extract_parameters, _extract_request_schema, _extract_success_response
#TODO: Вынести схемы в тестовые данные и вызывать их оттуда

ROOT_EMPTY = {"openapi": "3.0.3", "paths": {}, "components": {}}

def test_is_http_method_case_insensitive():
    assert _is_http_method("get")
    assert _is_http_method("GET")
    assert _is_http_method("pOsT")
    assert not _is_http_method("parameters")
    assert not _is_http_method("summary")

def test_paths_object_empty_returns_empty_list():
    assert extract_paths({"paths": {}}) == []

def test_path_item_ignores_non_http_keys_and_reads_operation():
    spec = {
        "paths": {
            "/ping": {
                "parameters": [{"name": "X-Req", "in": "header", "schema": {"type": "string"}}],
                "get": {
                    "summary": "Ping",
                    "responses": {"200": {"content": {"application/json": {"schema": {"type": "string"}}}}},
                },
                "description": "path-level meta that must be ignored by method loop",
            }
        }
    }
    eps = extract_paths(spec)
    assert len(eps) == 1
    e = eps[0]
    assert e.path == "/ping"
    assert e.method == "GET"
    assert e.summary == "Ping"  # взято с уровня Operation

def test_parameters_merge_order_and_override():
    path_item = {
        "parameters": [
            {"name": "app", "in": "path", "required": False, "schema": {"type": "string"}},
            {"name": "pipeline", "in": "path", "required": True, "schema": {"type": "string"}},
        ]
    }
    operation = {
        "parameters": [
            {"name": "app", "in": "path", "required": True, "schema": {"type": "string"}, "example": "shop"},
            {"name": "limit", "in": "query", "schema": {"type": "integer"}, "example": 50},
        ]
    }

    merged = _merge_parameters(path_item["parameters"], operation["parameters"])
    assert [(p["name"], p["in"]) for p in merged] == [
        ("app", "path"),          # перекрыт operation'ом
        ("pipeline", "path"),     # остался от path-level
        ("limit", "query"),       # новый из operation
    ]

    # полный объект параметров после _extract_parameters
    params = _extract_parameters(path_item, operation, ROOT_EMPTY)
    assert [(p.name, p.in_, p.type, p.example) for p in params] == [
        ("app", "path", "string", "shop"),
        ("pipeline", "path", "string", None),
        ("limit", "query", "integer", 50),
    ]

def test_extract_parameters_defaults_and_skips_invalid():
    path_item = {"parameters": [{"schema": {"type": "string"}}]}  # нет name/in -> пропуск
    operation = {"parameters": [{"name": "q", "in": "query", "schema": {"type": "string"}}]}
    params = _extract_parameters(path_item, operation, ROOT_EMPTY)
    assert len(params) == 1
    assert params[0].name == "q" and params[0].in_ == "query" and params[0].type == "string"

    # если schema отсутствует -> type по умолчанию "string" (текущая логика)
    path_item2 = {"parameters": [{"name": "X-Req", "in": "header"}]}
    operation2 = {"parameters": []}
    params2 = _extract_parameters(path_item2, operation2, ROOT_EMPTY)
    assert params2[0].type == "string"


def test_extract_request_schema_prefers_application_json():
    op = {
        "requestBody": {
            "content": {
                "text/plain": {"schema": {"type": "string"}},
                "application/json": {"schema": {"type": "object", "properties": {"a": {"type": "string"}}}},
            }
        }
    }
    sch = _extract_request_schema(op, ROOT_EMPTY)
    assert sch == {"type": "object", "properties": {"a": {"type": "string"}}}

    # отсутствие application/json
    op2 = {"requestBody": {"content": {"text/plain": {"schema": {"type": "string"}}}}}
    assert _extract_request_schema(op2, ROOT_EMPTY) is None

    # отсутствие requestBody
    assert _extract_request_schema({}, ROOT_EMPTY) is None

def test_extract_success_response_prefers_200_then_201_then_202():
    responses = {
        "201": {"content": {"application/json": {"schema": {"type": "object", "properties": {"ok": {"type": "boolean"}}}}}},
        "200": {"content": {"application/json": {"schema": {"type": "string"}}}},
        "202": {"content": {"application/json": {"schema": {"type": "integer"}}}},
    }
    code, sch = _extract_success_response(responses, ROOT_EMPTY)
    assert code == "200" and sch == {"type": "string"}

    # только 201
    code2, sch2 = _extract_success_response({"201": {"content": {"application/json": {"schema": {"type": "integer"}}}}}, ROOT_EMPTY)
    assert code2 == "201" and sch2 == {"type": "integer"}

    # есть код, но нет application/json
    code3, sch3 = _extract_success_response({"200": {"content": {"text/plain": {"schema": {"type": "string"}}}}}, ROOT_EMPTY)
    assert code3 == "200" and sch3 is None

    # нет 200/201/202
    code4, sch4 = _extract_success_response({"404": {"description": "not found"}}, ROOT_EMPTY)
    assert code4 is None and sch4 is None


def test_extract_paths_assembles_endpoint_from_layers():
    spec = {
        "paths": {
            "/{app}/files/{box}/{location}": {
                "parameters": [
                    {"name": "app", "in": "path", "schema": {"type": "string"}},
                    {"name": "box", "in": "path", "schema": {"type": "string"}},
                    {"name": "location", "in": "path", "schema": {"type": "string"}},
                ],
                "get": {
                    "summary": "List files",
                    "parameters": [{"name": "limit", "in": "query", "schema": {"type": "integer"}, "example": 10}],
                    "responses": {
                        "200": {"content": {"application/json": {"schema": {"type": "array", "items": {"type": "string"}}}}}
                    },
                },
                "servers": [{"url": "https://ignored.example"}],  # игнорируется
            },
            "/health": {
                "GET": {  # проверяем регистр
                    "summary": "Health",
                    "responses": {"200": {"content": {"text/plain": {"schema": {"type": "string"}}}}},
                }
            },
        }
    }

    eps = extract_paths(spec)
    # два эндпоинта: GET для /files и GET для /health
    assert len(eps) == 2

    e_files = next(e for e in eps if e.path.startswith("/{app}/files"))
    assert e_files.method == "GET"
    assert e_files.summary == "List files"
    assert [(p.name, p.in_, p.type, p.example) for p in e_files.parameters] == [
        ("app", "path", "string", None),
        ("box", "path", "string", None),
        ("location", "path", "string", None),
        ("limit", "query", "integer", 10),
    ]
    assert e_files.response_success_code == "200"
    assert e_files.response_schema == {"type": "array", "items": {"type": "string"}}
    assert e_files.request_schema is None  # requestBody отсутствует

    e_health = next(e for e in eps if e.path == "/health")
    assert e_health.method == "GET"
    assert e_health.summary == "Health"
    assert e_health.response_success_code == "200"
    assert e_health.response_schema is None  # нет application/json
    assert e_health.parameters == []

def test_success_response_via_ref_is_resolved():
    spec = {
        "paths": {
            "/t": {
                "get": {
                    "responses": {
                        "200": {"$ref": "#/components/responses/trial"}
                    }
                }
            }
        },
        "components": {
            "responses": {
                "trial": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/TrialResponse"}
                        }
                    }
                }
            },
            "schemas": {
                "TrialResponse": {
                    "type": "object",
                    "properties": {"id": {"type": "string"}, "ok": {"type": "boolean"}},
                    "required": ["id", "ok"]
                }
            }
        }
    }
    eps = extract_paths(spec)
    assert eps[0].response_success_code == "200"
    assert eps[0].response_schema == {
        "type": "object",
        "properties": {"id": {"type": "string"}, "ok": {"type": "boolean"}},
        "required": ["id", "ok"]
    }


def test_extract_success_response_via_ref_resolves_schema():
    spec = {
        "paths": {},
        "components": {
            "responses": {
                "trial": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/TrialResponse"}
                        }
                    }
                }
            },
            "schemas": {
                "TrialResponse": {
                    "type": "object",
                    "properties": {"id": {"type": "string"}, "status": {"enum": ["CREATED", "DONE"]}},
                    "required": ["id", "status"]
                }
            }
        }
    }
    responses = {"200": {"$ref": "#/components/responses/trial"}}
    code, sch = _extract_success_response(responses, spec)
    assert code == "200"
    assert sch == {
        "type": "object",
        "properties": {"id": {"type": "string"}, "status": {"enum": ["CREATED", "DONE"]}},
        "required": ["id", "status"],
    }

def test_extract_parameters_via_ref_is_resolved():
    spec = {
        "paths": {},
        "components": {
            "parameters": {
                "Q": {"name": "q", "in": "query", "required": False, "schema": {"type": "string"}, "example": "hello"}
            }
        }
    }
    path_item = {"parameters": [{"$ref": "#/components/parameters/Q"}]}
    operation = {"parameters": []}
    params = _extract_parameters(path_item, operation, spec)
    assert len(params) == 1
    assert (params[0].name, params[0].in_, params[0].type, params[0].example) == ("q", "query", "string", "hello")