import pytest
import tempfile
import yaml
import os

from test_case_generation.models.OpenAPISpec import OpenAPISpec
from test_case_generation.models.TestCase import TestCase
from test_case_generation.services.TestCaseGenerator import TestCaseGenerator

MINIMAL_OPENAPI = {
    "openapi": "3.0.0",
    "info": {"title": "Test API", "version": "1.0.0"},
    "servers": [{"url": "http://localhost:1234"}],
    "paths": {
        "/todos": {
            "get": {
                "summary": "List All todos",
                "operationId": "getTodos",
                "responses": {"200": {"description": "OK"}}
            },
            "post": {
                "summary": "Create todo",
                "operationId": "createTodo",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {"type": "object", "properties": {"name": {"type": "string"}}},
                        }
                    }
                },
                "responses": {"201": {"description": "Created"}}
            }
        },
        "/todos/{todoId}": {
            "get": {
                "summary": "Get todo",
                "operationId": "getTodo",
                "parameters": [
                    {"name": "todoId", "in": "path", "required": True, "schema": {"type": "string"}}
                ],
                "responses": {"200": {"description": "OK"}}
            }
        }
    },
    "components": {
        "schemas": {
            "todo": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "completed": {"type": "boolean"}
                }
            }
        }
    }
}

@pytest.fixture
def openapi_file():
    fd, path = tempfile.mkstemp(suffix=".yaml")
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        yaml.dump(MINIMAL_OPENAPI, f, allow_unicode=True)
    yield path
    os.remove(path)

def test_openapi_spec_load(openapi_file):
    spec = OpenAPISpec(openapi_file)
    assert spec.servers[0]['url'] == "http://localhost:1234"
    assert "/todos" in spec.paths
    assert "todo" in spec.parsed_schemas
    assert any(op.operation_id == "getTodos" for op in spec.parsed_operations)

def test_get_base_url(openapi_file):
    spec = OpenAPISpec(openapi_file)
    assert spec.get_base_url() == "http://localhost:1234"

def test_schema_object_structure(openapi_file):
    spec = OpenAPISpec(openapi_file)
    schema = spec.parsed_schemas["todo"]
    assert schema.name == "todo"
    assert schema.schema_type == "object"
    assert "name" in schema.properties

def test_generate_test_cases(openapi_file):
    spec = OpenAPISpec(openapi_file)
    gen = TestCaseGenerator(spec)
    gen.generate_test_cases()
    assert len(gen.test_cases) == len(spec.parsed_operations)
    tc = gen.test_cases[0]
    assert isinstance(tc, TestCase)
    # Проверяем что имя, endpoint и summary есть
    assert tc.name
    assert tc.endpoint
    assert tc.operation_summary

def test_testcase_to_yaml_dict(openapi_file):
    spec = OpenAPISpec(openapi_file)
    gen = TestCaseGenerator(spec)
    gen.generate_test_cases()
    d = gen.test_cases[0].to_yaml_dict()
    assert "Тест-кейс" in d
    assert "Endpoint" in d
    assert "Ожидаемый результат" in d

def test_make_path_placeholder():
    # Тестируем логику _make_path_placeholder напрямую
    from test_case_generation.services.TestCaseGenerator import TestCaseGenerator
    class DummySpec:
        def get_base_url(self): return ""
        parsed_operations = []  # Нужно для инициализации TestCaseGenerator
    gen = TestCaseGenerator(DummySpec())
    assert gen._make_path_placeholder("todoId") == "<id_todo>"
    assert gen._make_path_placeholder("id") == "<id>"
    assert gen._make_path_placeholder("other") == "<other>"


def test_build_query_string():
    from test_case_generation.services.TestCaseGenerator import TestCaseGenerator
    class DummySpec:
        def get_base_url(self): return ""
        parsed_operations = []  # Нужно для инициализации TestCaseGenerator
    gen = TestCaseGenerator(DummySpec())
    assert gen._build_query_string({}) == ''
    assert gen._build_query_string({'a': '1'}) == '?a=1'
    assert gen._build_query_string({'a': '1', 'b': '2'}) in ['?a=1&b=2', '?b=2&a=1']

def test_gen_stub_value():
    from test_case_generation.services.TestCaseGenerator import TestCaseGenerator
    class DummySpec:
        def get_base_url(self): return ""
        parsed_operations = []  # Нужно для инициализации TestCaseGenerator
    gen = TestCaseGenerator(DummySpec())
    assert gen._gen_stub_value('string', None) == "test_value (::String)"
    assert gen._gen_stub_value('boolean', None) == "true"
    assert gen._gen_stub_value('integer', None) == "12345"
    assert gen._gen_stub_value('number', None) == "3.14"
    assert gen._gen_stub_value('string', 'date') == "test_value (::Date)"

