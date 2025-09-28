from typing import Any, Dict
from utils.ReferenceResolver import ReferenceResolver

def generate_request_body(schema: Dict[str, Any], reference_resolver: ReferenceResolver) -> Any:
    if not schema:
        return None

    if isinstance(schema, dict) and '$ref' in schema:
        schema = reference_resolver.resolve_ref(schema)

    schema_type = schema.get('type')

    if 'allOf' in schema:
        for sub in schema['allOf']:
            sub_resolved = reference_resolver.resolve_ref(sub)
            if isinstance(sub_resolved, dict) and sub_resolved.get('type') == 'object':
                schema = sub_resolved
                schema_type = 'object'
                break
    elif 'oneOf' in schema:
        schema = reference_resolver.resolve_ref(schema['oneOf'][0])
        schema_type = schema.get('type')
    elif 'anyOf' in schema:
        schema = reference_resolver.resolve_ref(schema['anyOf'][0])
        schema_type = schema.get('type')


    if 'example' in schema:
        return schema['example']
    if 'default' in schema:
        return schema['default']
    if 'enum' in schema and isinstance(schema['enum'], list) and schema['enum']:
        return schema['enum'][0]

    if schema_type == 'object' or ('properties' in schema and schema_type is None):
        body = {}
        for prop, prop_attrs in (schema.get('properties') or {}).items():
            body[prop] = generate_request_body(prop_attrs, reference_resolver)  # рекурсия с разыменованием внутри
        if 'additionalProperties' in schema:
            ap = schema['additionalProperties']
            ap_schema = reference_resolver.resolve_ref(ap, reference_resolver) if isinstance(ap, dict) else {}
            body["<additionalPropertyKey>"] = generate_request_body(ap_schema, reference_resolver)
        return body

    if schema_type == 'array':
        item_schema = schema.get('items', {})
        return [generate_request_body(item_schema, reference_resolver)]

    # простые типы
    if schema_type in ('string', 'integer', 'number', 'boolean'):
        return f"<{schema_type}>"

    return "<value>"
