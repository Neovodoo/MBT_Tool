from typing import Any, Dict

def generate_request_body(schema: Dict[str, Any], components_schemas: Dict[str, Any]) -> Any:
    if not schema:
        return None

    if '$ref' in schema:
        ref = schema['$ref'].split('/')[-1]
        schema = components_schemas.get(ref, {})

    schema_type = schema.get('type')

    if schema_type == 'object':
        body = {}
        for prop, prop_attrs in schema.get('properties', {}).items():
            body[prop] = generate_request_body(prop_attrs, components_schemas)
        return body

    if schema_type == 'array':
        item_schema = schema.get('items', {})
        return [generate_request_body(item_schema, components_schemas)]

    # Для простых типов
    return f"<{schema_type}>"
