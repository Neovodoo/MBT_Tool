from dataclasses import dataclass

spec_key = 'example'

@dataclass
class ExampleField:
    example: str

def extract_example_field(parameter_details) -> str:
    example = parameter_details.get(spec_key) or "Пример отсутствует"
    return example