from typing import Any, Dict, Optional, Set


class ReferenceResolver:
    yaml_data: dict

    def __init__(self):
        pass

    def _lookup_pointer(self, pointer: str) -> Dict[str, Any]:
        # поддерживаем только внутренние ссылки вида "#/a/b"
        if not (isinstance(pointer, str) and pointer.startswith("#/")):
            return {}
        node: Dict[str, Any] = self.yaml_data
        for raw in pointer[2:].split("/"):
            key = raw.replace("~1", "/").replace("~0", "~")
            nxt = node.get(key)
            if not isinstance(nxt, dict):
                return {}
            node = nxt
        return node

    def resolve_ref(self, node: Any, seen: Optional[Set[str]] = None) -> Any:
        # если это не dict или нет $ref — возвращаем как есть
        if not isinstance(node, dict) or "$ref" not in node:
            return node
        ref = node["$ref"]
        if not (isinstance(ref, str) and ref.startswith("#/")):
            # внешние ссылки (URL/файл) в этом прототипе не поддерживаем
            return node
        seen = seen or set()
        if ref in seen:  # защита от циклов
            return node
        seen.add(ref)
        target = self._lookup_pointer(ref)
        # рекурсивно, потому что и цель может быть ссылкой
        return self.resolve_ref(target, seen)

    def initialize_data(self, yaml_data):
        self.yaml_data=yaml_data


reference_resolver = ReferenceResolver()