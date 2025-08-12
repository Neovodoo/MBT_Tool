import yaml
from .models import Endpoint, Parameter

def load_yaml(file_path: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as f:
        yaml_data = yaml.safe_load(f)
    return yaml_data


HTTP_METHODS = {"get", "post", "put", "delete", "patch", "options", "head"}

def _is_http_method(name: str) -> bool:
    return name.lower() in HTTP_METHODS

def _extract_summary(details: dict) -> str:
    return details.get('summary', '')

# Метод для формирования финального списка параметров, если они повторяются на уровне пути и на уровне метода берется описание параметра из уровня метода
def _merge_parameters(path_level_params, method_level_params):
    merged = {}
    order = []  # храним порядок ключей

    def key_for(p):
        name = p.get('name')
        _in = p.get('in')
        return (name, _in) if name and _in else ('$', id(p))

    for p in path_level_params or []:
        k = key_for(p)
        if k not in merged:
            order.append(k)
        merged[k] = p

    for p in method_level_params or []:
        k = key_for(p)
        if k not in merged:
            order.append(k)
        merged[k] = p  # перекрываем, если есть совпадение по (name,in)

    return [merged[k] for k in order]

def _extract_parameters(path: dict, details: dict) -> list:

    path_level_params = path.get('parameters', [])
    method_level_params = details.get('parameters', [])
    parameters_list = _merge_parameters(path_level_params, method_level_params)

    params = []
    for p in parameters_list:

        name = p.get('name')
        in_ = p.get('in')

        #Логика обработки значение типа и схемы TODO: Нужно описать, понять и доработать добавив поддержку ссылок на схему
        schema = p.get('schema') or {}
        p_type = schema.get('type', 'string')
        example = p.get('example', schema.get('example'))

        # Какая то логика по обработке ссылок вместо типов данных  TODO: Нужно описать, понять и доработать
        if not name or not in_:
            # Пропускаем “сырые” ссылки/$ref — обработаем в следующем шаге
            continue

        params.append(Parameter(
            name=name,
            in_=in_,
            required=p.get('required', False),
            type=p_type,
            example=example,
        ))
    return params

def _extract_request_schema(details: dict):
    return (details.get('requestBody', {})
                  .get('content', {})
                  .get('application/json', {})
                  .get('schema'))

def _extract_success_response(responses: dict):
    success_code = next((c for c in ['200', '201', '202'] if c in responses), None)
    schema = None
    if success_code:
        content = responses[success_code].get('content', {})
        if 'application/json' in content:
            schema = content['application/json'].get('schema')
    return success_code, schema

def extract_paths(openapi_spec: dict) -> list:
    endpoints = []
    for path_block, path_items in openapi_spec.get('paths', {}).items():
        for http_method, method_details in path_items.items():
            if not _is_http_method(http_method):
                continue

            summary = _extract_summary(method_details)

            merged_parameters = _extract_parameters(path_items, method_details)

            request_schema = _extract_request_schema(method_details)

            success_code, response_schema = _extract_success_response(method_details.get('responses', {}))

            endpoints.append(Endpoint(
                path=path_block,
                method=http_method.upper(),
                summary=summary,
                parameters=merged_parameters,
                request_schema=request_schema,
                response_success_code=success_code,
                response_schema=response_schema,
            ))
    return endpoints

