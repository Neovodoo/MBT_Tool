from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class Step:
    path: str = ""
    method: str = ""

    def extract_data(self, path: str, method: str) -> None:
        self.extract_path(path)
        self.extract_method(method)

    def extract_path(self, path: str) -> str:
        self.path = path
        return self.path

    def extract_method(self, method: str) -> str:
        self.method = method.upper()
        return self.method


    def to_text(self) -> List[str]:
        lines = ["- Метод: " + self.method]
        lines.append("")
        lines.append("- URL: " + self.path)
        return lines