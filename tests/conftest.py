import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

class DummyResolver:
    #Заглушка ReferenceResolver 
    def __init__(self, mapping=None):
        self.mapping = mapping or {}

    def resolve_ref(self, node):
        if not isinstance(node, dict):
            return node
        ref = node.get("$ref")
        if not ref:
            return node
        return self.mapping.get(ref, node)

@pytest.fixture
def resolver_empty():
    return DummyResolver()

@pytest.fixture
def resolver_with_mapping():
    return DummyResolver(mapping={
        "#/schemas/User": {"type": "object"},
        "#/parameters/QueryPage": {
            "name": "page",
            "in": "query",
            "required": False,
            "schema": {"type": "integer"},
            "example": 1
        }
    })
