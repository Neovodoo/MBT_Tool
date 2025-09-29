from dataclasses import dataclass

spec_key = 'in'

@dataclass
class InField:
    in_: str

def extract_in_field(parameter_details) -> str:
    in_ = parameter_details.get(spec_key) or "Позиция параметра в запросе отсутствует"
    return in_