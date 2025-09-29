import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from utils.ReferenceResolver import ReferenceResolver
from utils.BodyGenerator import generate_request_body


SEPARATOR_LINE = "-" * 20

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
        if self.expectedResponseBody is None or "additional_info" in self.expectedResponseBody:
            lines.append("Тело ответа отсутствует")
        else:
            lines.extend(json.dumps(self.expectedResponseBody, ensure_ascii=False, indent=2).splitlines())
        lines.append("")
        lines.append(SEPARATOR_LINE)
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

    def extract_body(self, method_details: Dict[str, Any], resolver: ReferenceResolver) -> Any:
        responses = method_details.get("responses", {}) or {}
        code = self.extract_status(method_details)
        resp = responses.get(code) if code else None
        if isinstance(resp, dict) and "$ref" in resp:
            resp = resolver.resolve_ref(resp) or {}
        content = (resp or {}).get("content", {})
        media = content.get("application/json") or next(iter(content.values()), None)
        body = None
        if isinstance(media, dict):
            schema = media.get("schema") or {}
            body = generate_request_body(schema, resolver)
        self.expectedResponseBody = body
        return body