from generator.parser import load_yaml, extract_paths
from generator.generator import generate_test_cases

if __name__ == "__main__":
    data = load_yaml('api.yaml')
    endpoints = extract_paths(data)
    test_cases = generate_test_cases(endpoints)

    print("Сгенерированные тест-кейсы:\n")
    for tc in test_cases:
        print(tc.to_text())
        print('-' * 30)
