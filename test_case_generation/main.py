import argparse
from test_case_generation.models.OpenAPISpec import OpenAPISpec
from test_case_generation.services.TestCaseGenerator import TestCaseGenerator

def main():
    parser = argparse.ArgumentParser(
        description="Генерация тест-кейсов на основе OpenAPI спецификации"
    )
    parser.add_argument(
        "spec_path",
        help="Путь к OpenAPI спецификации (.yaml или .yml)"
    )
    parser.add_argument(
        "--txt-out",
        default="test_cases.txt",
        help="Файл для сохранения тест-кейсов в текстовом формате (по умолчанию: test_cases.txt)"
    )
    parser.add_argument(
        "--yaml-out",
        default="test_cases.yaml",
        help="Файл для сохранения тест-кейсов в YAML формате (по умолчанию: test_cases.yaml)"
    )
    parser.add_argument(
        "--no-print",
        action="store_true",
        help="Не выводить тест-кейсы в консоль"
    )

    args = parser.parse_args()

    spec = OpenAPISpec(args.spec_path)
    generator = TestCaseGenerator(spec)
    generator.generate_test_cases()

    if not args.no_print:
        generator.print_test_cases()

    generator.save_test_cases(args.txt_out)
    generator.save_test_cases_yaml(args.yaml_out)

    print(f"Готово! Файлы '{args.txt_out}' и '{args.yaml_out}' созданы.")

if __name__ == "__main__":
    main()
