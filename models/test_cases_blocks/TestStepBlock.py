from dataclasses import dataclass, field
from typing import List
from models.Step import Step
from utils.ReferenceResolver import ReferenceResolver

SEPARATOR_LINE = "-" * 20

@dataclass
class TestStepsBlock:
    steps: List[Step] = field(default_factory=list)

    def fillTestStepBlock(self, path: str, method: str, path_item: dict, method_details: dict, resolver: ReferenceResolver):
        for step in self.steps:
            if step.path == path and step.method.upper() == method.upper():
                step.extract_data(path, method)
                return step
        step = Step()
        step.extract_data(path, method, path_item, method_details, resolver)
        self.steps.append(step)
        return step

    def to_text(self) -> List[str]:
        lines = ["Шаги выполнения:"]
        if not self.steps:
            lines.append("Шаги отсутствуют в спецификации")
        else:
            for i, step in enumerate(self.steps, 1):
                lines.append(f"Шаг {i}:")
                lines.append("")
                lines.extend(step.to_text())
        lines.append("")
        lines.append(SEPARATOR_LINE)
        return lines

