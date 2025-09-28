import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class ExpectedResultBlock:
    expectedResponseStatus: str = ""
    expectedResponseBody: Any = None

    def to_text(self) -> List[str]:
        lines = [
            "Ожидаемый результат:",
            "\n",
            f"- Статус ответа: {self.expectedResponseStatus or '-'}",
            "\n"
            "- Тело ответа:",
        ]
        if self.expectedResponseBody is None:
            lines.append("Тело ответа отсутствует")
        else:
            lines.extend(json.dumps(self.expectedResponseBody, ensure_ascii=False, indent=2).splitlines())
        return lines

    def extract_status(self, method_details: Dict[str, Any]) -> Optional[str]:
        responses = method_details.get("responses", {}) or {}
        for code in ("200", "201", "202", "203", "204", "205", "206"):
            if code in responses:
                self.expectedResponseStatus = code
                return code
        if responses:
            self.expectedResponseStatus = next(iter(responses.keys()))
            return self.expectedResponseStatus
        self.expectedResponseStatus = ""
        return None