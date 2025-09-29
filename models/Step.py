from dataclasses import dataclass, field
from typing import List, Dict, Any
from models.parameter.Parameter import Parameter

@dataclass
class Step:
    path: str = ""
    method: str = ""
    path_parameters: List[Parameter] = field(default_factory=list)

    def extract_data(self, path: str, method: str, path_item: dict, method_details: dict) -> None:
        self.extract_path(path)
        self.extract_method(method)
        self.extract_path_parameters(path_item, method_details)

    def extract_path(self, path: str) -> str:
        self.path = path
        return self.path

    def extract_method(self, method: str) -> str:
        self.method = method.upper()
        return self.method

    def extract_path_parameters(self, path_item: dict, method_details: dict):
        parameters = Parameter.extract_data_for_parameters_list(path_item, method_details)
        for parameter in parameters:
            if parameter.in_ == "path":
                self.path_parameters.append(parameter)
        return self.path_parameters



    def to_text(self) -> List[str]:
        lines = ["- Метод: " + self.method]
        lines.append("")
        lines.append("- URL: " + self.path)
        lines.append("")
        lines.append("- Параметры пути:")
        for p in self.path_parameters:
            lines.append(p.to_line())
        return lines