import pytest

from utils.ReferenceResolver import ReferenceResolver, reference_resolver


def test_initialize_data_and_module_instance():
    rr = ReferenceResolver()
    data = {"a": {"b": {}}}
    rr.initialize_data(data)
    assert rr.yaml_data is data

    assert isinstance(reference_resolver, ReferenceResolver)


def test_lookup_pointer_invalid_inputs():
    rr = ReferenceResolver()
    rr.initialize_data({"a": {}})

    # не строка
    assert rr._lookup_pointer(123) == {}
    # не начинается с "#/"
    assert rr._lookup_pointer("#a") == {}
    assert rr._lookup_pointer("abc") == {}
    # базовый "#/" без ключей -> пусто
    assert rr._lookup_pointer("#/") == {}


def test_lookup_pointer_success_and_not_dict_midway():
    rr = ReferenceResolver()
    rr.initialize_data({"a": {"b": {"c": {"x": 1}}}})
    assert rr._lookup_pointer("#/a/b/c") == {"x": 1}

    # середина пути не dict -> {}
    rr.initialize_data({"a": {"b": 5}})
    assert rr._lookup_pointer("#/a/b") == {}


def test_lookup_pointer_escaped_tokens():

    rr = ReferenceResolver()
    rr.initialize_data({
        "root": {
            "x~y": {
                "z/w": {"ok": True}
            }
        }
    })

    out = rr._lookup_pointer("#/root/x~0y/z~1w")
    assert out == {"ok": True}



def test_resolve_ref_returns_input_when_no_ref_or_not_dict():
    rr = ReferenceResolver()
    rr.initialize_data({})
    assert rr.resolve_ref({"a": 1}) == {"a": 1}  # нет $ref
    assert rr.resolve_ref(42) == 42              # не dict


def test_resolve_ref_external_ref_left_as_is():
    rr = ReferenceResolver()
    rr.initialize_data({})
    node = {"$ref": "http://example.com/Ext"}
    # Внешние ссылки не поддерживаются
    assert rr.resolve_ref(node) is node


def test_resolve_ref_internal_simple():
    rr = ReferenceResolver()
    rr.initialize_data({
        "components": {"schemas": {"User": {"type": "object", "title": "User"}}}
    })
    node = {"$ref": "#/components/schemas/User"}
    out = rr.resolve_ref(node)
    assert out == {"type": "object", "title": "User"}


def test_resolve_ref_chain():
    rr = ReferenceResolver()
    rr.initialize_data({
        "components": {"schemas": {
            "A": {"$ref": "#/components/schemas/B"},
            "B": {"type": "object", "title": "Real"}
        }}
    })
    node = {"$ref": "#/components/schemas/A"}
    out = rr.resolve_ref(node)
    assert out == {"type": "object", "title": "Real"}


def test_resolve_ref_cycle_protection():
    rr = ReferenceResolver()
    rr.initialize_data({
        "A": {"$ref": "#/B"},
        "B": {"$ref": "#/A"},
    })
    node = {"$ref": "#/A"}
    out = rr.resolve_ref(node)
    # Должны  не зациклиться
    assert isinstance(out, dict) and "$ref" in out

