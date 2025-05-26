from typing import Optional, Dict, List, Any


class SchemaObject:
    """
    Описывает схему (из components/schemas).
    """

    def __init__(
            self,
            name: str,
            schema_type: str = '',
            schema_format: str = '',
            properties: Optional[Dict[str, 'SchemaObject']] = None,
            required: Optional[List[str]] = None,
            description: str = '',
            enum_values: Optional[List[str]] = None,
            ref: str = '',
            example: Any = None
    ):
        self.name = name
        self.schema_type = schema_type
        self.schema_format = schema_format
        self.properties = properties if properties else {}
        self.required = required if required else []
        self.description = description
        self.enum_values = enum_values if enum_values else []
        self.ref = ref
        self.example = example

    def __repr__(self) -> str:
        return (
            f"SchemaObject(name={self.name}, type={self.schema_type}, format={self.schema_format}, "
            f"properties={list(self.properties.keys())}, required={self.required}, "
            f"enum_values={self.enum_values}, ref={self.ref}, example={self.example})"
        )