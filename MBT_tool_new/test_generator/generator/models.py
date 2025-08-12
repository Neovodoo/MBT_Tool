import json
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


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
    request_schema: Optional[dict] = None  # Схема для тела запроса
    response_success_code: Optional[str] = None  # Код для тела ответа
    response_schema: Optional[dict] = None  # Схема для тела ответа

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
class TestStep:
    method: str
    url: str
    headers: Optional[Dict[str, Any]] = None
    path_params: Optional[Dict[str, Any]] = None
    query_params: Optional[Dict[str, Any]] = None
    body: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    expected_status: Optional[int] = None
    expected_body: Optional[Dict[str, Any]] = None


@dataclass
class TestCase:
    name: str
    description: str
    steps: List[TestStep] = field(default_factory=list)

    def to_text(self) -> str:
        text = f"Тест-кейс: {self.name}\nОписание: {self.description}\n\n"

        def steps_to_text(steps: List[TestStep], title: str) -> str:
            result = f"{title}:\n"
            if not steps:
                return result + "  Нет\n"
            for step in steps:
                result += (
                    f"  - Описание шага: {step.description or 'Нет описания'}\n"
                    f"    Метод: {step.method}\n"
                    f"    URL: {step.url}\n"
                    f"    Заголовки: {step.headers or 'Нет'}\n"
                    f"    Параметры пути: {step.path_params or 'Нет'}\n"
                    f"    Параметры запроса: {step.query_params or 'Нет'}\n"
                    f"    Тело запроса:\n"
                    f"{json.dumps(step.body, indent=2, ensure_ascii=False) if step.body else '      Нет'}\n"
                    f"    Ожидаемый статус: {step.expected_status or 'Не указан'}\n"
                    f"    Ожидаемое тело ответа:\n"
                    f"{json.dumps(step.expected_body, indent=2, ensure_ascii=False) if step.expected_body else '      Не указано'}\n"
                )
            return result

        text += steps_to_text(self.steps, "Шаги выполнения")
        return text