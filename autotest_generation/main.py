import argparse
from autotest_generation.services.AutotestRunner import run_autotests

def main():
    parser = argparse.ArgumentParser(description="Генерация и запуск автотестов по YAML")
    parser.add_argument("--yaml-file", required=True, help="Путь к YAML-файлу с тест-кейсами")
    parser.add_argument("--allure-results", default="allure-results", help="Куда сложить результаты Allure")
    args = parser.parse_args()
    run_autotests(args.yaml_file, args.allure_results)

if __name__ == "__main__":
    main()
