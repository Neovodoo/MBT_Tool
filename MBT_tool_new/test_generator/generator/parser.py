import yaml
from .models import Endpoint, Parameter
from .resolver import resolve_ref

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

def _extract_parameters(path_items: dict, method_details: dict, openapi_spec: dict) -> list:

    path_level_params = path_items.get('parameters', [])
    method_level_params = method_details.get('parameters', [])
    parameters_list = _merge_parameters(path_level_params, method_level_params)

    params = []
    for p in parameters_list:

        if isinstance(p, dict) and '$ref' in p:
            p = resolve_ref(p, openapi_spec)

        name = p.get('name')
        in_ = p.get('in')

        #Логика обработки значение типа и схемы TODO: Нужно описать, понять и доработать добавив поддержку ссылок на схему
        schema = p.get('schema') or {}
        if isinstance(schema, dict) and '$ref' in schema:
            schema = resolve_ref(schema, openapi_spec)
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

def _extract_request_schema(method_details: dict, openapi_spec: dict):
    rb = method_details.get('requestBody')
    if not rb:
        return None
    if isinstance(rb, dict) and '$ref' in rb:
        rb = resolve_ref(rb, openapi_spec)

    content = rb.get('content', {}) if isinstance(rb, dict) else {}
    app_json = content.get('application/json')
    if not app_json:
        return None
    schema = app_json.get('schema')
    if isinstance(schema, dict) and '$ref' in schema:
        schema = resolve_ref(schema, openapi_spec)
    return schema

def _extract_success_response(responses: dict, openapi_spec: dict):
    success_code = next((c for c in ['200', '201', '202'] if c in responses), None) #TODO: Сделать регулярку для выбора кодов, чтобы начинались с 20х
    schema = None
    if success_code:
        resp = responses[success_code]
        if isinstance(resp, dict) and '$ref' in resp:
            resp = resolve_ref(resp, openapi_spec)
        content = resp.get('content', {}) if isinstance(resp, dict) else {}
        app_json = content.get('application/json')
        if app_json:
            schema = app_json.get('schema')
            if isinstance(schema, dict) and '$ref' in schema:
                schema = resolve_ref(schema, openapi_spec)
    return success_code, schema

def extract_paths(openapi_spec: dict) -> list:
    endpoints = []
    for path_block, path_items in openapi_spec.get('paths', {}).items():
        for http_method, method_details in path_items.items():
            if not _is_http_method(http_method):
                continue

            summary = _extract_summary(method_details)

            merged_parameters = _extract_parameters(path_items, method_details, openapi_spec)

            request_schema = _extract_request_schema(method_details, openapi_spec)

            success_code, response_schema = _extract_success_response(method_details.get('responses', {}), openapi_spec)

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

