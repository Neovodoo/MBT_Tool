from dataclasses import dataclass

@dataclass
class Endpoint:
    path: str
    method: str
    summary: str

@dataclass
class TestCase:
    name: str
    endpoint: Endpoint
    description: str

    def to_text(self) -> str:
        return (
            f"Тест-кейс: {self.name}\n"
            f"Метод: {self.endpoint.method}\n"
            f"Путь: {self.endpoint.path}\n"
            f"Описание: {self.description}\n"
        )