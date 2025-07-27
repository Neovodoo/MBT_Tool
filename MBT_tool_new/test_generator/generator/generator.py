from .models import Endpoint, TestCase


def generate_test_cases(endpoints: list) -> list:
    test_cases = []
    for ep in endpoints:
        name = ep.summary or f"{ep.method} {ep.path}"
        description = f"Позитивный тест вызова {ep.method} {ep.path}"

        test_case = TestCase(
            name=name,
            endpoint=ep,
            description=description
        )
        test_cases.append(test_case)
    return test_cases
