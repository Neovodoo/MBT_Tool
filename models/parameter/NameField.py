from dataclasses import dataclass

spec_key = 'name'

@dataclass
class NameField:
    name: str


def extract_name_field(parameter_details) -> str:
    name = parameter_details.get(spec_key) or "Имя отсутствует"
    return name