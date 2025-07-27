from generator.parser import load_yaml, extract_paths

if __name__ == "__main__":
    data = load_yaml('api.yaml')
    endpoints = extract_paths(data)

    print("Найденные эндпоинты:\n")
    for endpoint in endpoints:
        print(f"Путь: {endpoint['path']}")
        print(f"Метод: {endpoint['method']}")
        print(f"Описание: {endpoint['summary']}")
        print('-' * 20)
