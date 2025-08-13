from typing import Any, Dict
from .resolver import resolve_ref

def generate_request_body(schema: Dict[str, Any], openapi_spec: Dict[str, Any]) -> Any:
    if not schema:
        return None

        # всегда сначала разворачиваем ссылку
    if isinstance(schema, dict) and '$ref' in schema:
        schema = resolve_ref(schema, openapi_spec)

    schema_type = schema.get('type')

    # 'allOf'/'oneOf'/'anyOf' встречаются часто — поддержим базово
    if 'allOf' in schema:
        # наивный merge: просто берём первую "object"-схему
        for sub in schema['allOf']:
            sub_resolved = resolve_ref(sub, openapi_spec)
            if isinstance(sub_resolved, dict) and sub_resolved.get('type') == 'object':
                schema = sub_resolved
                schema_type = 'object'
                break
    elif 'oneOf' in schema:
        schema = resolve_ref(schema['oneOf'][0], openapi_spec)
        schema_type = schema.get('type')
    elif 'anyOf' in schema:
        schema = resolve_ref(schema['anyOf'][0], openapi_spec)
        schema_type = schema.get('type')

    # быстрые хелперы — если есть example/default/enum
    if 'example' in schema:
        return schema['example']
    if 'default' in schema:
        return schema['default']
    if 'enum' in schema and isinstance(schema['enum'], list) and schema['enum']:
        return schema['enum'][0]

    if schema_type == 'object' or ('properties' in schema and schema_type is None):
        body = {}
        for prop, prop_attrs in (schema.get('properties') or {}).items():
            body[prop] = generate_request_body(prop_attrs, openapi_spec)  # рекурсия с разыменованием внутри
        # additionalProperties как карта
        if 'additionalProperties' in schema:
            ap = schema['additionalProperties']
            ap_schema = resolve_ref(ap, openapi_spec) if isinstance(ap, dict) else {}
            body["<additionalPropertyKey>"] = generate_request_body(ap_schema, openapi_spec)
        return body

    if schema_type == 'array':
        item_schema = schema.get('items', {})
        return [generate_request_body(item_schema, openapi_spec)]

    # простые типы
    if schema_type in ('string', 'integer', 'number', 'boolean'):
        return f"<{schema_type}>"

    return "<value>"



#TODO: Избавиться от заглушки в виде типа строки для параметров запроса если не указан тип