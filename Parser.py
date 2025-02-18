import yaml
import sys


def parse_openapi_endpoints(file_path: str) -> dict:
    """
    Парсит OpenAPI спецификацию и возвращает эндпоинты с методами
    """
    with open(file_path, 'r') as f:
        spec = yaml.safe_load(f)

    endpoints = {}

    # Шаг 1: Получаем все эндпоинты из раздела 'paths'
    for path in spec.get('paths', {}):
        endpoints[path] = []

        # Шаг 2: Для каждого эндпоинта получаем методы
        for method in spec['paths'][path]:
            # Фильтруем только HTTP-методы
            if method.lower() in {'get', 'post', 'put', 'delete', 'patch'}:
                endpoints[path].append(method.upper())

    return endpoints

def print_endpoints(endpoints: dict):
    """Печатает эндпоинты и методы в читаемом формате"""
    for path, methods in endpoints.items():
        print(f"\n{path}:")
        for method in methods:
            print(f"  → {method}")


def generate_test_cases(endpoints: dict) -> list:
    """
    Генерирует тест-кейсы с предусловиями и постусловиями.
    """
    test_cases = []
    test_number = 1

    # Сопоставление методов с их зависимостями
    dependency_map = {
        'GET': {'pre': ['POST'], 'post': ['DELETE']},
        'PUT': {'pre': ['POST'], 'post': ['DELETE']},
        'DELETE': {'pre': ['POST'], 'post': []},
        'POST': {'pre': [], 'post': ['DELETE']}  # Для POST проверяем отсутствие данных через GET
    }

    for path in sorted(endpoints.keys()):
        for method in sorted(endpoints[path], key=lambda m: ['GET', 'POST', 'PUT', 'DELETE'].index(m)):
            test_case = {
                'number': test_number,
                'method': method,
                'path': path,
                'preconditions': [],
                'steps': [],
                'postconditions': []
            }

            # Определяем базовый путь для ресурса (например, /todos/{todoId} → /todos)
            base_path = path.split('{')[0].rstrip('/') if '{' in path else path

            # Генерация предусловий
            for dep_method in dependency_map.get(method, {}).get('pre', []):
                # Для GET/PUT/DELETE: создаем ресурс через POST
                if dep_method == 'POST':
                    pre_path = base_path
                    test_case['preconditions'].append(
                        f"Отправить запрос типа '{dep_method}' для эндпоинта '{pre_path}'"
                    )

            # Основной шаг теста
            test_case['steps'].append(
                f"Отправить запрос типа '{method}' для эндпоинта '{path}'"
            )

            # Генерация постусловий (очистка данных)
            for dep_method in dependency_map.get(method, {}).get('post', []):
                if dep_method == 'DELETE' and '{' in path:
                    test_case['postconditions'].append(
                        f"Отправить запрос типа '{dep_method}' для эндпоинта '{path}'"
                    )

            test_cases.append(test_case)
            test_number += 1

    return test_cases


def print_test_cases(test_cases: list):
    """Форматированный вывод с условиями"""
    print("\nСгенерированные тест-кейсы:")
    for case in test_cases:
        print(f"\nТест {case['number']}:")
        if case['preconditions']:
            print("  Предусловия:")
            for pre in case['preconditions']:
                print(f"    → {pre}")
        print("  Шаги:")
        for step in case['steps']:
            print(f"    → {step}")
        if case['postconditions']:
            print("  Постусловия:")
            for post in case['postconditions']:
                print(f"    → {post}")



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python openapi_parser.py <openapi_file.yml>")
        sys.exit(1)

    file_path = sys.argv[1]
    endpoints = parse_openapi_endpoints(file_path)

    # Выводим базовую информацию
    print_endpoints(endpoints)

    # Генерируем и выводим тест-кейсы
    test_cases = generate_test_cases(endpoints)
    print_test_cases(test_cases)
    print("For git")
