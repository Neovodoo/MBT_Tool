from models.TestCase import TestCase

from typing import List

class Writer:

    def __init__(self, cases: List[TestCase]):
        self.cases = cases

    def to_text(self) -> str:
        return "\n".join([case.to_text() for case in self.cases])

    def write(self, out_path: str) -> None:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(self.to_text())