import yaml
import pytest
from MBT_tool_new.test_generator.generator.body_generator import generate_request_body
from MBT_tool_new.test_generator.generator.parser import _extract_request_schema

def test_generate_body_resolves_nested_refs():
    spec = {
        "components": {
            "schemas": {
                "Inner": {"type": "object", "properties": {"v": {"type": "integer"}}},
                "Outer": {"type": "object", "properties": {"in": {"$ref": "#/components/schemas/Inner"}}}
            }
        }
    }

    body = generate_request_body({"$ref": "#/components/schemas/Outer"}, spec)
    assert body == {"in": {"v": "<integer>"}}



#TODO: Вынести схемы в тестовые данные и вызывать их оттуда
def _build_spec_with_request_body_ref():
    """
    Спецификация: POST /items, где requestBody -> $ref на components.requestBodies.CreateItem,
    а внутри content.application/json.schema -> $ref на components.schemas.CreateItem
    """
    return {
        "openapi": "3.0.3",
        "paths": {
            "/items": {
                "post": {
                    "summary": "Create item",
                    "requestBody": {"$ref": "#/components/requestBodies/CreateItem"},
                    "responses": {"201": {"description": "created"}},
                }
            }
        },
        "components": {
            "requestBodies": {
                "CreateItem": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/CreateItem"}
                        }
                    }
                }
            },
            "schemas": {
                "CreateItem": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "count": {"type": "integer"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["name", "count"]
                }
            }
        }
    }


def test_extract_request_schema_via_requestBodies_ref_is_resolved():
    """
    Проверяем, что _extract_request_schema умеет развернуть:
      requestBody ($ref -> components.requestBodies) -> content.application/json.schema
      и затем schema ($ref -> components.schemas)
    """
    spec = _build_spec_with_request_body_ref()
    op = spec["paths"]["/items"]["post"]

    schema = _extract_request_schema(op, spec)  # <-- ВАЖНО: передаём корень спецификации
    expected = spec["components"]["schemas"]["CreateItem"]
    assert schema == expected, "Должны получить развёрнутую схему из components.schemas.CreateItem"


def test_generate_request_body_uses_resolved_request_schema():
    """
    По развёрнутой схеме запросов генерируем «скелет» JSON.
    Проверяем типовые плейсхолдеры для string/integer и 1 элемент массива.
    """
    spec = _build_spec_with_request_body_ref()
    op = spec["paths"]["/items"]["post"]
    schema = _extract_request_schema(op, spec)

    body = generate_request_body(schema, spec)  # <-- тоже передаём root
    assert body == {
        "name": "<string>",
        "count": "<integer>",
        "tags": ["<string>"],
    }