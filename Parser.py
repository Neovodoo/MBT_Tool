import yaml
import argparse
from typing import Dict, List


class OpenAPISpec:
    """Класс для работы с OpenAPI спецификацией"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.spec_data = self._load_spec()

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


class TestCase:
    """Класс для представления тест-кейса"""

    def __init__(self, case_id: int, endpoint: str, method: str):
        self.case_id = case_id
        self.endpoint = endpoint
        self.method = method

    def print(self):
        """Вывод тест-кейса в консоль"""
        print(f"Тест кейс {self.case_id}")
        print("Шаги:")
        print(f"Отправить запрос типа {self.method} для эндпоинта ({self.endpoint})")
        print()


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
                self.test_cases.append(
                    TestCase(case_id, endpoint, method)
                )
                case_id += 1

    def print_cases(self):
        """Вывод всех сгенерированных кейсов"""
        for case in self.test_cases:
            case.print()


def main():
    # Настройка аргументов командной строки
    parser = argparse.ArgumentParser(description='Generate test cases from OpenAPI spec')
    parser.add_argument('spec_file', type=str, help='Path to OpenAPI YAML file')
    args = parser.parse_args()

    # Инициализация и запуск генерации
    spec = OpenAPISpec(args.spec_file)
    generator = TestCaseGenerator(spec)
    generator.generate()
    generator.print_cases()


if __name__ == "__main__":
    main()