from dataclasses import dataclass, field
from typing import List, Dict, Any
from models.parameter.Parameter import Parameter
from utils.ReferenceResolver import ReferenceResolver

@dataclass
class Step:
    path: str = ""
    method: str = ""
    path_parameters: List[Parameter] = field(default_factory=list)
    query_parameters: List[Parameter] = field(default_factory=list)
    headers: List[Parameter] = field(default_factory=list)

    def extract_data(self, path: str, method: str, path_item: dict, method_details: dict, resolver: ReferenceResolver) -> None:
        self.extract_path(path)
        self.extract_method(method)
        self.extract_path_parameters(path_item, method_details, resolver)
        self.extract_query_parameters(path_item, method_details, resolver)
        self.extract_headers(path_item, method_details, resolver)

    def extract_path(self, path: str) -> str:
        self.path = path
        return self.path

    def extract_method(self, method: str) -> str:
        self.method = method.upper()
        return self.method

    def extract_path_parameters(self, path_item: dict, method_details: dict, resolver: ReferenceResolver):
        parameters = Parameter.extract_data_for_parameters_list(path_item, method_details, resolver)
        for parameter in parameters:
            if parameter.in_ == "path":
                self.path_parameters.append(parameter)
        return self.path_parameters

    def extract_query_parameters(self, path_item: dict, method_details: dict, resolver: ReferenceResolver):
        parameters = Parameter.extract_data_for_parameters_list(path_item, method_details, resolver)
        for parameter in parameters:
            if parameter.in_ == "query":
                self.query_parameters.append(parameter)
        return self.query_parameters

    def extract_headers(self, path_item: dict, method_details: dict, resolver: ReferenceResolver):
        parameters = Parameter.extract_data_for_parameters_list(path_item, method_details, resolver)
        for parameter in parameters:
            if parameter.in_ == "header":
                self.headers.append(parameter)
        return self.headers



    def to_text(self) -> List[str]:
        lines = ["- Метод: " + self.method]
        lines.append("")
        lines.append("- URL: " + self.path)
        lines.append("")

        lines.append("- Заголовки запроса:")
        if len(self.headers) == 0:
            lines.append("")
            lines.append("      - Заголовки отсутствуют")
        for h in self.headers:
            lines.append(h.to_line())

        lines.append("")
        lines.append("- Параметры пути:")
        if len(self.path_parameters)== 0:
            lines.append("")
            lines.append("      - Параметры пути отсутствуют")
        for p in self.path_parameters:
            lines.append(p.to_line())

        lines.append("")
        lines.append("- Параметры запроса:")
        if len(self.query_parameters) == 0:
            lines.append("")
            lines.append("      - Параметры запроса отсутствуют")
        for p in self.query_parameters:
            lines.append(p.to_line())

        return lines