import yaml
from .models import Endpoint

def load_yaml(file_path: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as f:
        yaml_data = yaml.safe_load(f)
    return yaml_data


def extract_paths(yaml_data: dict) -> list:
    paths = yaml_data.get('paths', {})
    endpoints = []

    for path, methods in paths.items():
        for method, details in methods.items():
            summary = details.get('summary', '')

            endpoint = Endpoint(
                path=path,
                method=method.upper(),
                summary=summary
            )

            endpoints.append(endpoint)

    return endpoints
