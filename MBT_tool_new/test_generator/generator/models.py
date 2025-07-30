from dataclasses import dataclass, field
from typing import Optional, List


#TODO: Избавиться от влияния порядка объявления классов на их параметры
@dataclass
class Parameter:
    name: str
    in_: str  # слово in – ключевое в Python, поэтому используем in_
    required: bool
    type: str
    example: Optional[str] = None

@dataclass
class Endpoint:
    path: str
    method: str
    summary: str
    parameters: List[Parameter] = field(default_factory=list)

    def generate_example_url(self) -> str:
        url = self.path
        query_params = []

        for param in self.parameters:
            example_value = param.example or f"<{param.name}>"
            if param.in_ == 'path':
                url = url.replace(f"{{{param.name}}}", str(example_value))
            elif param.in_ == 'query':
                query_params.append(f"{param.name}={example_value}")

        if query_params:
            url += '?' + '&'.join(query_params)

        return url

@dataclass
class TestCase:
    name: str
    endpoint: Endpoint
    description: str

    def to_text(self) -> str:
        # TODO: Вынести формирование текста для параметров в отдельный метод
        params_text = ""
        if self.endpoint.parameters:
            params_text = "Параметры запроса:\n"
            for param in self.endpoint.parameters:
                params_text += (
                    f" - {param.name} ({param.in_}), "
                    f"тип: {param.type}, "
                    f"{'обязательный' if param.required else 'необязательный'}, "
                    f"пример: {param.example or 'нет'}\n"
                )
        else:
            params_text = "Параметры: отсутствуют\n"


        return (
            f"Тест-кейс: {self.name}\n"
            f"Метод: {self.endpoint.method}\n"
            f"Путь: {self.endpoint.path}\n"
            f"Описание: {self.description}\n"
            f"{params_text}"
        )