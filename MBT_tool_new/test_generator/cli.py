from generator.parser import load_yaml, extract_paths
from generator.generator import save_test_cases_to_file
from generator.body_generator import generate_request_body
from generator.models import TestStep, TestCase

if __name__ == "__main__":
    yaml_data = load_yaml('api_pipeline.yaml')
    endpoints = extract_paths(yaml_data)
    base_url = "http://localhost:8001"
    components_schemas = yaml_data.get('components', {}).get('schemas', {})

    test_cases = []

    for ep in endpoints:
        # генерация тела запроса из схемы
        body = generate_request_body(ep.request_schema, components_schemas) if ep.request_schema else None

        expected_body = generate_request_body(ep.response_schema, components_schemas) if ep.response_schema else None

        # создание TestStep с расширенными параметрами
        step = TestStep(
            method=ep.method,
            url=base_url + ep.generate_example_url(),
            headers={"Authorization": "Basic <token>"},
            path_params={p.name: f"<{p.type}>" for p in ep.parameters if p.in_ == 'path'},
            query_params={p.name: f"<{p.type}>" for p in ep.parameters if p.in_ == 'query'},
            body=body,
            description=ep.summary,
            expected_status=int(ep.response_success_code) if ep.response_success_code else 200,
            expected_body=expected_body
        )

        test_case = TestCase(
            name=ep.summary or f"{ep.method} {ep.path}",
            description=ep.summary,
            steps=[step]
        )

        test_cases.append(test_case)

    # Сохраняем в файл
    save_test_cases_to_file(test_cases, 'generated_test_cases_detailed.txt')
    print("Подробные тест-кейсы успешно сохранены!")
