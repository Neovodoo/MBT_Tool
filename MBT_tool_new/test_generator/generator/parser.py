import yaml

def load_yaml(file_path: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as f:
        yaml_data = yaml.safe_load(f)
    return yaml_data
