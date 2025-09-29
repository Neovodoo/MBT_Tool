from dataclasses import dataclass
from utils.ReferenceResolver import ReferenceResolver

spec_key = 'schema'

@dataclass
class DatatypeField:
    datatype: str

def extract_datatype_field(parameter_details, resolver: ReferenceResolver) -> str:
    schema = parameter_details.get('schema') or {}
    if isinstance(schema, dict) and '$ref' in schema:
        schema = resolver.resolve_ref(schema)
    p_type = schema.get('type', 'Тип данных отсутствует')
    return p_type