from dataclasses import dataclass, field
from typing import List
from models.Step import Step
from utils.ReferenceResolver import ReferenceResolver

SEPARATOR_LINE = "-" * 20

@dataclass
class PostconditionsBlock:
    steps: List[Step] = field(default_factory=list)

    def fill_postconditions_block(self, path: str, tested_method: str, path_item: dict, resolver: ReferenceResolver):
        self.steps.clear()
        if tested_method.lower() in ("get", "put") and "delete" in path_item:
            delete_details = path_item.get("delete") or {}
            step = Step()
            step.extract_data(path, "delete", path_item, delete_details, resolver)
            self.steps.append(step)

    def to_text(self) -> List[str]:
        lines = ["Постусловия:"]
        if not self.steps:
            lines.append("")
            lines.append("  - Постусловия отсутствуют")
        else:
            for i, step in enumerate(self.steps, 1):
                lines.append(f"Шаг {i}:")
                lines.append("")
                lines.extend(step.to_text())
        lines.append("")
        lines.append(SEPARATOR_LINE)
        return lines