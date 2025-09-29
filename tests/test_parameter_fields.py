import json
import pytest

from models.parameter.DataTypeField import extract_datatype_field
from models.parameter.ExampleField import extract_example_field
from models.parameter.InField import extract_in_field
from models.parameter.NameField import extract_name_field
from models.parameter.RequiredField import extract_required_field
from models.parameter.Parameter import Parameter

# DataTypeField
def test_extract_datatype_plain_type(resolver_empty):
    p = {"schema": {"type": "string"}}
    assert extract_datatype_field(p, resolver_empty) == "string"

def test_extract_datatype_via_ref(resolver_with_mapping):
    p = {"schema": {"$ref": "#/schemas/User"}}
    assert extract_datatype_field(p, resolver_with_mapping) == "object"

def test_extract_datatype_missing_type(resolver_empty):
    p = {"schema": {}}
    assert extract_datatype_field(p, resolver_empty) == "Тип данных отсутствует"

# ExampleField
@pytest.mark.parametrize("payload,expected", [
    ({"example": {"k": 1}}, {"k": 1}),
    ({}, "Пример отсутствует"),
])
def test_extract_example_field(payload, expected):
    assert extract_example_field(payload) == expected

# InField
@pytest.mark.parametrize("payload,expected", [
    ({"in": "query"}, "query"),
    ({}, "Позиция параметра в запросе отсутствует"),
])
def test_extract_in_field(payload, expected):
    assert extract_in_field(payload) == expected

# NameField
@pytest.mark.parametrize("payload,expected", [
    ({"name": "id"}, "id"),
    ({}, "Имя отсутствует"),
])
def test_extract_name_field(payload, expected):
    assert extract_name_field(payload) == expected

# RequiredField
@pytest.mark.parametrize("payload,expected", [
    ({"required": True}, True),
    ({"required": False}, False),
    ({}, False),
])
def test_extract_required_field(payload, expected):
    assert extract_required_field(payload) is expected

# Parameter pipeline: merge / extract / to_line
def test_merge_and_extract_parameters(resolver_with_mapping):
    # path-level параметры
    path_item = {
        "parameters": [
            {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}},
            {"$ref": "#/parameters/QueryPage"},
            {"schema": {"type": "string"}, "example": "ignored"}  # без name/in
        ]
    }
    # method-level перекрывает path-level для (name,id)
    method_details = {
        "parameters": [
            {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}, "example": "m"},
            {"name": "search", "in": "query", "required": False, "schema": {"type": "string"}, "example": "q"},
        ]
    }

    params = Parameter.extract_data_for_parameters_list(path_item, method_details, resolver_with_mapping)
    assert len(params) == 3

    by_name = {p.name: p for p in params}

    # id — тип и пример взяты из method-level
    assert "id" in by_name
    assert by_name["id"].in_ == "path"
    assert by_name["id"].datatype == "string"
    assert by_name["id"].example == "m"
    assert by_name["id"].required is True

    # search — обычный query
    assert "search" in by_name
    assert by_name["search"].in_ == "query"
    assert by_name["search"].datatype == "string"
    assert by_name["search"].example == "q"
    assert by_name["search"].required is False

    # безымянный — проверяем дефолты
    unnamed = [p for p in params if p.name == "Имя отсутствует"]
    assert len(unnamed) == 1
    p = unnamed[0]
    assert p.in_ == "Позиция параметра в запросе отсутствует"

    assert p.example == "ignored"
    assert p.required is False

def test_parameter_to_line_variants():
    # example: dict →  json
    p_dict = Parameter(name="meta", in_="header", required=True, example={"a": 1}, datatype="object")
    line_dict = p_dict.to_line()
    assert "meta: Пример: <" + json.dumps({"a": 1}, ensure_ascii=False, separators=(",", ":")) + ">" in line_dict
    assert "Обязательный: Да" in line_dict

    # example: None → "Пример отсутствует"
    p_none = Parameter(name="x", in_="header", required=False, example=None, datatype="string")
    line_none = p_none.to_line()
    assert "x: Пример: <Пример отсутствует>" in line_none
    assert "Тип данных: <string>" in line_none
    assert "Обязательный: Нет" in line_none

    # example: строка
    p_str = Parameter(name="q", in_="query", required=False, example="abc", datatype="string")
    line_str = p_str.to_line()
    assert "q: Пример: <abc>" in line_str
    assert "Расположение: query" in line_str
