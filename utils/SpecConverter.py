import yaml
from typing import Any, Dict

class OpenAPISpecConverter:

    @staticmethod
    def convert_spec_to_dict(path: str) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError:
            raise ValueError("Некорректный формат OpenAPI документа")
        return data