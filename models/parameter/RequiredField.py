from dataclasses import dataclass

spec_key = 'required'

@dataclass
class RequiredField:
    required: bool

def extract_required_field(parameter_details) -> bool:
    required = parameter_details.get(spec_key) or False
    return required