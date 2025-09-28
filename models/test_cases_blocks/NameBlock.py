import uuid
from dataclasses import dataclass
from typing import List, Dict, Any


SEPARATOR_LINE = "-" * 20


@dataclass
class NameBlock:
    uuid: str = ""
    name: str = ""
    description: str = ""


    def to_text(self) -> List[str]:
        return [
            "",
            f" - Контрольный пример: {self.name}",
            "\n",
            f" - Уникальный идентификатор: {self.uuid}",
            "\n",
            f" - Описание: {self.description}",
            "",
            SEPARATOR_LINE,
        ]

    def generate_uuid(self) -> str:
        self.uuid = str(uuid.uuid4())
        return self.uuid

    def extract_description(self, method_details: Dict[str, Any]) -> str:
        self.description = str(method_details.get("description") or "")
        if not self.description:
            self.description = f"Описание отсутствует"
        return self.description

    def generate_name(self, path: str, method: str) -> str:
        self.name = str("Проверка метода <" + method + "> для пути <" + path + ">")
        return self.name
