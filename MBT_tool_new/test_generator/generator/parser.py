import yaml
from .models import Endpoint, Parameter

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

            # Извлекаем параметры
            params_data = details.get('parameters', [])
            parameters = []

            for p in params_data:
                param = Parameter(
                    name=p['name'],
                    in_=p['in'],
                    required=p.get('required', False),
                    type=p['schema']['type'],
                    example=p.get('example')
                )
                parameters.append(param)

            endpoint = Endpoint(
                path=path,
                method=method.upper(),
                summary=summary,
                parameters=parameters
            )

            endpoints.append(endpoint)

    return endpoints
