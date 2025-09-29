import json
from dataclasses import dataclass
from models.parameter.NameField import NameField, extract_name_field
from models.parameter.InField import InField, extract_in_field
from models.parameter.RequiredField import RequiredField, extract_required_field
from models.parameter.ExampleField import ExampleField, extract_example_field

spec_key = 'parameters'

@dataclass
class Parameter:
    name: str
    in_: str
    required: bool
    example: str


    # Метод для формирования финального списка параметров, если они повторяются на уровне пути и на уровне метода берется описание параметра из уровня метода
    def _merge_parameters(path_level_params, method_level_params):
        merged = {}
        order = []

        def key_for(p):
            name = extract_name_field(p)
            in_ = extract_in_field(p)
            return (name, in_) if name and in_ else ('$', id(p))

        for p in path_level_params or []:
            k = key_for(p)
            if k not in merged:
                order.append(k)
            merged[k] = p

        for p in method_level_params or []:
            k = key_for(p)
            if k not in merged:
                order.append(k)
            merged[k] = p  # перекрываем, если есть совпадение по (name,in)

        return [merged[k] for k in order]


    def _create_parameters_list(path_item: dict, method_details: dict):
        path_level_params = path_item.get(spec_key, [])
        method_level_params = method_details.get(spec_key, [])
        parameters_list = Parameter._merge_parameters(path_level_params, method_level_params)
        return parameters_list

    def extract_data_for_parameters_list(path_item: dict, method_details: dict):
        parameters_list = Parameter._create_parameters_list(path_item, method_details)
        parameters = []
        for p in parameters_list:
            name = extract_name_field(p)
            in_ = extract_in_field(p)
            required = extract_required_field(p)
            example = extract_example_field(p)

            parameters.append(Parameter(
                name=name,
                in_=in_,
                required=required,
                example=example,
                        ))
        return parameters


    def to_line(self) -> str:
        required = "Да" if self.required else "Нет"
        example = self.example
        if isinstance(example, (dict, list)):
            ex_str = json.dumps(example, ensure_ascii=False, separators=(",", ":"))
        elif example is None:
            ex_str = "Пример отсутствует"
        else:
            ex_str = str(example)
        return f"       - {self.name}: Пример: <{ex_str or self.example}> (Расположение: {self.in_}; Обязательный: {required};)"


