import yaml
import argparse
from typing import Dict, List, Tuple, Any


class OpenAPISpec:
    """Класс для работы с OpenAPI спецификацией"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.spec_data = self._load_spec()
        self.components = self.spec_data.get('components', {}).get('schemas', {})

    def _load_spec(self) -> Dict:
        """Загрузка спецификации из файла"""
        with open(self.file_path, 'r') as file:
            return yaml.safe_load(file)

    def get_endpoints(self) -> List[str]:
        """Извлечение списка эндпоинтов"""
        return list(self.spec_data.get('paths', {}).keys())

    def get_methods_for_endpoint(self, endpoint: str) -> List[str]:
        """Извлечение методов для конкретного эндпоинта"""
        methods = self.spec_data['paths'][endpoint].keys()
        return [m.upper() for m in methods if m.lower() in {
            'get', 'post', 'put', 'delete', 'patch', 'head', 'options', 'trace'
        }]

    def get_success_responses(self, endpoint: str, method: str) -> List[Tuple[str, str]]:
        """Извлечение успешных ответов (2xx) для метода"""
        responses = []
        method_data = self.spec_data['paths'][endpoint].get(method.lower())

        if method_data and 'responses' in method_data:
            for status_code, response in method_data['responses'].items():
                if status_code.startswith('2'):
                    body_schema = self._get_response_body(response) or "Пустое тело"
                    responses.append((status_code, body_schema))

        return responses

    def _get_response_body(self, response: Dict) -> str:
        """Генерация JSON-примера на основе схемы ответа"""
        content = response.get('content')
        if not content:
            return None

        media_type = next(iter(content.values()), {})
        schema = media_type.get('schema', {})

        return self._generate_example(schema) if schema else None

    def _generate_example(self, schema: Dict) -> Any:
        """Рекурсивная генерация примеров данных по схеме"""
        if '$ref' in schema:
            return self._handle_reference(schema['$ref'])

        schema_type = schema.get('type')
        example = schema.get('example')

        if example is not None:
            return example

        if schema_type == 'object':
            return self._generate_object(schema)
        if schema_type == 'array':
            return self._generate_array(schema)
        if schema_type == 'string':
            return "string_value"
        if schema_type == 'number':
            return 123.45
        if schema_type == 'integer':
            return 42
        if schema_type == 'boolean':
            return True

        return "Неопределенная схема"

    def _generate_object(self, schema: Dict) -> Dict:
        """Генерация объекта с полями"""
        properties = schema.get('properties', {})
        required = schema.get('required', [])

        return {
            prop: self._generate_example(prop_schema)
            for prop, prop_schema in properties.items()
            if prop in required or not required
        }

    def _generate_array(self, schema: Dict) -> List:
        """Генерация массива"""
        items_schema = schema.get('items', {})
        return [self._generate_example(items_schema)]

    def _handle_reference(self, ref: str) -> Any:
        """Обработка ссылок на компоненты"""
        schema_name = ref.split('/')[-1]
        component = self.components.get(schema_name, {})
        return self._generate_example(component) if component else "Ссылочная схема"


class TestCase:
    """Класс для представления тест-кейса"""

    def __init__(self, case_id: int, endpoint: str, method: str, status: str, body: Any):
        self.case_id = case_id
        self.endpoint = endpoint
        self.method = method
        self.status = status
        self.body = body or "Пустое тело"

    def print(self):
        """Вывод тест-кейса в консоль"""
        print(f"Тест кейс {self.case_id}")
        print("Шаги:")
        print(f"Отправить запрос типа {self.method} для эндпоинта ({self.endpoint})")
        print("Ожидаемый результат:")
        print(f"Получен ответ: статус {self.status} и тело запроса\n  {self._format_body()}")
        print()

    def _format_body(self) -> str:
        """Форматирование тела ответа для вывода"""
        if isinstance(self.body, dict) or isinstance(self.body, list):
            return yaml.dump(self.body, allow_unicode=True, sort_keys=False)
        return str(self.body)


class TestCaseGenerator:
    """Класс для генерации тест-кейсов"""

    def __init__(self, openapi_spec: OpenAPISpec):
        self.openapi_spec = openapi_spec
        self.test_cases: List[TestCase] = []

    def generate(self):
        """Основной метод генерации кейсов"""
        case_id = 1
        for endpoint in self.openapi_spec.get_endpoints():
            for method in self.openapi_spec.get_methods_for_endpoint(endpoint):
                responses = self.openapi_spec.get_success_responses(endpoint, method)

                if not responses:
                    responses = [("Нет статусов из группы 200", "Пустое тело")]

                for status, body in responses:
                    self.test_cases.append(
                        TestCase(case_id, endpoint, method, status, body)
                    )
                    case_id += 1

    def print_cases(self):
        """Вывод всех сгенерированных кейсов"""
        for case in self.test_cases:
            case.print()


def main():
    parser = argparse.ArgumentParser(description='Generate test cases from OpenAPI spec')
    parser.add_argument('spec_file', type=str, help='Path to OpenAPI YAML file')
    args = parser.parse_args()

    spec = OpenAPISpec(args.spec_file)
    generator = TestCaseGenerator(spec)
    generator.generate()
    generator.print_cases()


if __name__ == "__main__":
    main()