import pytest

from utils.BodyGenerator import generate_request_body
from utils.ReferenceResolver import ReferenceResolver


@pytest.fixture
def resolver():
    rr = ReferenceResolver()
    rr.initialize_data({})
    return rr



def test_returns_none_for_empty_schema(resolver):
    assert generate_request_body({}, resolver) is None
    assert generate_request_body(None, resolver) is None


def test_top_level_ref_is_resolved(resolver):
    resolver.initialize_data({
        "defs": {
            "S": {"type": "string"}
        }
    })
    out = generate_request_body({"$ref": "#/defs/S"}, resolver)
    assert out == "<string>"


def test_allof_picks_first_object_schema(resolver):
    # allOf с несколькими подсхемами, среди них есть object
    schema = {
        "allOf": [
            {"type": "string"},
            {"type": "object", "properties": {"x": {"type": "integer"}}}
        ]
    }
    out = generate_request_body(schema, resolver)
    assert out == {"x": "<integer>"}


def test_oneof_first_is_used(resolver):
    schema = {
        "oneOf": [
            {"type": "integer"},
            {"type": "string"},
        ]
    }
    out = generate_request_body(schema, resolver)
    assert out == "<integer>"


def test_anyof_first_is_used(resolver):
    schema = {
        "anyOf": [
            {"type": "number"},
            {"type": "boolean"},
        ]
    }
    out = generate_request_body(schema, resolver)
    assert out == "<number>"


# example/default/enum приоритеты

def test_example_has_priority(resolver):
    schema = {"type": "string", "example": "SAMPLE", "default": "DEF", "enum": ["E1", "E2"]}
    assert generate_request_body(schema, resolver) == "SAMPLE"

def test_default_when_no_example(resolver):
    schema = {"type": "integer", "default": 42}
    assert generate_request_body(schema, resolver) == 42

def test_enum_when_no_example_or_default(resolver):
    schema = {"type": "string", "enum": ["first", "second"]}
    assert generate_request_body(schema, resolver) == "first"


def test_object_with_properties_and_recursion(resolver):
    resolver.initialize_data({
        "defs": {"Inner": {"type": "boolean"}}
    })
    schema = {
        "type": "object",
        "properties": {
            "a": {"type": "string"},
            "b": {"type": "array", "items": {"type": "integer"}},
            "c": {"$ref": "#/defs/Inner"},
        }
    }
    out = generate_request_body(schema, resolver)
    assert out == {"a": "<string>", "b": ["<integer>"], "c": "<boolean>"}

def test_object_without_type_but_with_properties(resolver):
    schema = {
        "properties": {
            "x": {"type": "number"}
        }
    }
    out = generate_request_body(schema, resolver)
    assert out == {"x": "<number>"}


def test_object_with_additional_properties_plain_schema(resolver):
    schema = {
        "type": "object",
        "properties": {"a": {"type": "string"}},
        "additionalProperties": {"type": "string"}  # без $ref
    }
    out = generate_request_body(schema, resolver)
    # ожидаем ключ плейсхолдер и сгенерированное значение
    assert out["a"] == "<string>"
    assert "<additionalPropertyKey>" in out
    assert out["<additionalPropertyKey>"] == "<string>"


def test_object_with_additional_properties_ref_raises_typeerror(resolver):

    resolver.initialize_data({
        "defs": {"Val": {"type": "string"}}
    })
    schema = {
        "type": "object",
        "additionalProperties": {"$ref": "#/defs/Val"}
    }
    with pytest.raises(TypeError):
        generate_request_body(schema, resolver)




def test_array_of_objects(resolver):
    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {"z": {"type": "boolean"}}
        }
    }
    out = generate_request_body(schema, resolver)
    assert out == [{"z": "<boolean>"}]


def test_array_with_empty_items_returns_list_with_none(resolver):
    schema = {"type": "array", "items": {}}
    out = generate_request_body(schema, resolver)
    assert out == [None]




@pytest.mark.parametrize("typ,expected", [
    ("string", "<string>"),
    ("integer", "<integer>"),
    ("number", "<number>"),
    ("boolean", "<boolean>"),
])
def test_primitives(typ, expected, resolver):
    assert generate_request_body({"type": typ}, resolver) == expected


def test_unknown_type_fallback(resolver):
    assert generate_request_body({"type": "weird"}, resolver) == "<value>"
