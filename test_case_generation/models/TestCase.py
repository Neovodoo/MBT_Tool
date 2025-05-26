from typing import Dict, List, Any


class TestCase:
    """
    Тест кейс в формате:
      ТЕСТ-КЕЙС <Имя>:
        Endpoint: ...
        Смысл: ...
        Описание: ...
        ПРЕДУСЛОВИЯ:
          1. ...
        ШАГИ:
          1. ...
        ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:
          1. ...
        ПОСТУСЛОВИЯ:
          1. ...

    Дополнительно: метод to_yaml_dict() возвращает структуру для вывода в формат YAML:
      Тест-кейс: <Имя теста>
      Endpoint: <Метод + путь>
      Смысл: <summary>
      Описание: <description>
      Предусловия: [ {Endpoint, Headers, Cookies, Body}, ... ]
      Шаги: [ {Endpoint, Headers, Cookies, Body}, ... ]
      Ожидаемый результат: {Статус, Body}
      Постусловия: [ {Endpoint, Headers, Cookies, Body}, ... ]
    """

    def __init__(
            self,
            name: str,
            preconditions: List[str],
            steps: List[str],
            expected: List[str],
            postconditions: List[str],
            endpoint: str = '',
            operation_summary: str = '',
            operation_description: str = ''
    ):
        self.name = name
        self.preconditions = preconditions
        self.steps = steps
        self.expected = expected
        self.postconditions = postconditions

        self.endpoint = endpoint  # Например: "GET /todos"
        self.operation_summary = operation_summary  # Смысл/summary
        self.operation_description = operation_description  # Описание

        # Храним также более структурные данные для YAML (без curl).
        # Будем заполнять при генерации (в _make_test_case).
        self.preconditions_struct: List[Dict[str, Any]] = []
        self.steps_struct: List[Dict[str, Any]] = []
        self.postconditions_struct: List[Dict[str, Any]] = []
        # Ожидаемый результат (статус, body) в виде dict
        self.expected_struct: Dict[str, Any] = {}

    def __str__(self) -> str:
        """
        Исходное текстовое оформление тест-кейса
        (с разделителями, предусловиями, шагами, post-условиями, выводом curl и т.д.).
        """
        separator_line = "=" * 70
        lines = []

        # Заголовок тест-кейса
        lines.append(separator_line)
        lines.append(f"ТЕСТ-КЕЙС: {self.name}")
        lines.append(separator_line)

        # Дополнительная информация об операции
        if self.endpoint:
            lines.append(f"Endpoint: {self.endpoint}")
        if self.operation_summary:
            lines.append(f"Смысл: {self.operation_summary}")
        if self.operation_description:
            lines.append(f"Описание: {self.operation_description}")
        lines.append("")  # пустая строка

        # Предусловия
        lines.append("ПРЕДУСЛОВИЯ:")
        if self.preconditions:
            for i, p in enumerate(self.preconditions, 1):
                lines.append(f"  {i}. {p}")
        else:
            lines.append("  — (Нет предусловий)")
        lines.append("")

        # Шаги
        lines.append("ШАГИ:")
        if self.steps:
            for i, s in enumerate(self.steps, 1):
                lines.append(f"  {i}. {s}")
        else:
            lines.append("  — (Нет шагов)")
        lines.append("")

        # Ожидаемый результат
        lines.append("ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:")
        if self.expected:
            for i, e in enumerate(self.expected, 1):
                lines.append(f"  {i}. {e}")
        else:
            lines.append("  — (Нет ожидаемого результата)")
        lines.append("")

        # Постусловия
        lines.append("ПОСТУСЛОВИЯ:")
        if self.postconditions:
            for i, post in enumerate(self.postconditions, 1):
                lines.append(f"  {i}. {post}")
        else:
            lines.append("  — (Нет постусловий)")
        lines.append(separator_line)
        lines.append("")

        return "\n".join(lines)

    def to_yaml_dict(self) -> Dict[str, Any]:
        """
        Возвращает структуру для сохранения в YAML:
        - Без вывода curl
        - С обобщёнными данными
        """
        return {
            "Тест-кейс": self.name,
            "Endpoint": self.endpoint,
            "Смысл": self.operation_summary,
            "Описание": self.operation_description,
            "Предусловия": self.preconditions_struct,
            "Шаги": self.steps_struct,
            "Ожидаемый результат": {
                "Статус": self.expected_struct.get("status", "xxx"),
                "Body": self.expected_struct.get("body", {})
            },
            "Постусловия": self.postconditions_struct
        }
