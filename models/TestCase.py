from dataclasses import dataclass, field
from typing import List, Dict, Any

from models.test_cases_blocks.NameBlock import NameBlock


SEPARATOR_LINE = "-" * 90


@dataclass
class TestCase:
    name_block: NameBlock

    def to_text(self) -> str:
        parts: List[str] = [SEPARATOR_LINE]
        parts.extend(self.name_block.to_text())
        return "\n".join(parts)

    @classmethod
    def generate_test_cases(cls, openapi_spec: Dict[str, Any]) -> List["TestCase"]:
        cases: List[TestCase] = []

        paths = openapi_spec.get("paths", {}) or {}
        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            for method in ("get", "post", "put", "delete", "patch", "options", "head"):
                if method not in path_item:
                    continue
                method_details = path_item.get(method) or {}


                name = NameBlock()
                name.generate_uuid()
                name.extract_description(method_details)
                name.generate_name(path, method)


                test_case = cls(
                    name_block=name
                )

                cases.append(test_case)
        return cases