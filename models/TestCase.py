from dataclasses import dataclass, field
from typing import List, Dict, Any

from models.test_cases_blocks.NameBlock import NameBlock
from models.test_cases_blocks.EnvironmentBlock import EnvironmentBlock
from models.test_cases_blocks.ExpectedResultBlock import ExpectedResultBlock

from utils.ReferenceResolver import reference_resolver


SEPARATOR_LINE = "-" * 90


@dataclass
class TestCase:
    name_block: NameBlock
    environment_block: EnvironmentBlock
    expected_result_block: ExpectedResultBlock

    def to_text(self) -> str:
        parts: List[str] = [SEPARATOR_LINE]
        parts.extend(self.name_block.to_text())
        parts.extend(self.environment_block.to_text())
        parts.extend(self.expected_result_block.to_text())
        return "\n".join(parts)

    @classmethod
    def generate_test_cases(cls, openapi_spec: Dict[str, Any]) -> List["TestCase"]:
        reference_resolver.initialize_data(openapi_spec)

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

                environment = EnvironmentBlock()
                environment.extract_servers(openapi_spec)


                expected_result = ExpectedResultBlock()
                expected_result.extract_status(method_details)
                expected_result.extract_body(method_details, reference_resolver)




                test_case = cls(
                    name_block=name,
                    environment_block=environment,
                    expected_result_block=expected_result
                )

                cases.append(test_case)
        return cases