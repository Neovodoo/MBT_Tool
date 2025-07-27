from generator.parser import load_yaml

if __name__ == "__main__":
    data = load_yaml('api.yaml')
    print(data)

