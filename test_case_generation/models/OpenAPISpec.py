from test_case_generation.models.SchemaObject import SchemaObject
from test_case_generation.models.Operation import Operation
from typing import Dict, List, Any
import yaml


class OpenAPISpec:
    """
    Хранит OpenAPI спецификацию:
    - servers, components, paths
    - parsed_schemas (dict of SchemaObject)
    - parsed_operations (list of Operation)
    """

    def __init__(self, spec_path: str):
        self.spec_path = spec_path
        self.raw_spec = self.load_spec()
        self.servers = self.raw_spec.get('servers', [])
        self.components = self.raw_spec.get('components', {})
        self.paths = self.raw_spec.get('paths', {})

        self.parsed_schemas: Dict[str, SchemaObject] = {}
        self.parsed_operations: List[Operation] = []

        self._parse_components_schemas()
        self._parse_operations()

    def load_spec(self) -> Dict[str, Any]:
        with open(self.spec_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def get_base_url(self) -> str:
        if not self.servers:
            return ''
        return self.servers[0].get('url', '')

    def _parse_components_schemas(self) -> None:
        schemas = self.components.get('schemas', {})
        for schema_name, schema_def in schemas.items():
            sobj = self._create_schema_object(schema_name, schema_def)
            self.parsed_schemas[schema_name] = sobj

    def _create_schema_object(self, name: str, schema_def: Dict[str, Any]) -> 'SchemaObject':
        ref = schema_def.get('$ref', '')
        s_type = schema_def.get('type', '')
        s_format = schema_def.get('format', '')
        desc = schema_def.get('description', '')
        props = schema_def.get('properties', {})
        required = schema_def.get('required', [])
        enum_vals = schema_def.get('enum', [])
        example = schema_def.get('example', None)

        parsed_props: Dict[str, SchemaObject] = {}
        for prop_name, prop_def in props.items():
            if isinstance(prop_def, dict):
                if '$ref' in prop_def:
                    parsed_props[prop_name] = SchemaObject(
                        name=prop_name,
                        ref=prop_def['$ref']
                    )
                else:
                    parsed_props[prop_name] = self._create_schema_object(prop_name, prop_def)

        return SchemaObject(
            name=name,
            schema_type=s_type,
            schema_format=s_format,
            properties=parsed_props,
            required=required,
            description=desc,
            enum_values=enum_vals,
            ref=ref,
            example=example
        )

    def _parse_operations(self) -> None:
        for path, path_item in self.paths.items():
            path_params = path_item.get('parameters', [])
            for key, method_obj in path_item.items():
                if key.lower() in ("get", "put", "post", "delete", "patch", "options", "head"):
                    summary = method_obj.get('summary', '')
                    description = method_obj.get('description', '')
                    operation_id = method_obj.get('operationId', '')
                    method_level_params = method_obj.get('parameters', [])

                    all_params = path_params + method_level_params
                    rb = method_obj.get('requestBody', {})
                    resp = method_obj.get('responses', {})

                    op = Operation(
                        method=key,
                        path=path,
                        summary=summary,
                        description=description,
                        operation_id=operation_id,
                        parameters=all_params,
                        request_body=rb,
                        responses=resp
                    )
                    self.parsed_operations.append(op)

    def __repr__(self):
        return (f"OpenAPISpec(\n"
                f"  servers={self.servers},\n"
                f"  components_schemas={list(self.parsed_schemas.keys())},\n"
                f"  paths={list(self.paths.keys())},\n"
                f"  operations_count={len(self.parsed_operations)}\n"
                f")")