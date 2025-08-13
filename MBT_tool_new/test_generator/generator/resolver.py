# resolver.py
from typing import Any, Dict, Optional, Set

def _lookup_pointer(root: Dict[str, Any], pointer: str) -> Dict[str, Any]:
    # поддерживаем только внутренние ссылки вида "#/a/b"
    if not (isinstance(pointer, str) and pointer.startswith("#/")):
        return {}
    node: Dict[str, Any] = root
    for raw in pointer[2:].split("/"):
        key = raw.replace("~1", "/").replace("~0", "~")
        nxt = node.get(key)
        if not isinstance(nxt, dict):
            return {}
        node = nxt
    return node

def resolve_ref(node: Any, root: Dict[str, Any], seen: Optional[Set[str]] = None) -> Any:
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
    target = _lookup_pointer(root, ref)
    # рекурсивно, потому что и цель может быть ссылкой
    return resolve_ref(target, root, seen)
