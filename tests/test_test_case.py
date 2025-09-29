import pytest
import types

import models.TestCase as tc_mod



class FakeResolver:
    def __init__(self):
        self.initialized_with = None
    def initialize_data(self, spec):
        self.initialized_with = spec


class FakeNameBlock:
    def __init__(self):
        self.uuid = ""
        self.name = ""
        self.description = ""
        self.generated = False
        self.desc_from = None
        self.name_from = None

    def generate_uuid(self):
        self.uuid = "UUID-123"
        self.generated = True
        return self.uuid

    def extract_description(self, method_details):
        self.desc_from = method_details
        self.description = method_details.get("description") or "Описание отсутствует"
        return self.description

    def generate_name(self, path, method):
        self.name_from = (path, method)
        self.name = f"Проверка метода <{method}> для пути <{path}>"
        return self.name

    def to_text(self):
        return ["NB"]


class FakeEnvironmentBlock:
    def __init__(self):
        self.servers = None
        self.spec = None

    def extract_servers(self, spec):
        self.spec = spec
        self.servers = [s.get("url") for s in (spec.get("servers") or []) if isinstance(s.get("url"), str)]
        return self.servers

    def to_text(self):
        return ["EB"]


class FakePreconditionsBlock:
    def __init__(self):
        self.called_with = None

    def fill_preconditions_block(self, path, method, path_item, resolver):
        self.called_with = (path, method, path_item, resolver)

    def to_text(self):
        return ["PRE"]


class FakeTestStepsBlock:
    def __init__(self):
        self.called_with = None

    def fillTestStepBlock(self, path, method, path_item, method_details, resolver):
        self.called_with = (path, method, path_item, method_details, resolver)
        return types.SimpleNamespace()

    def to_text(self):
        return ["STEP"]


class FakeExpectedResultBlock:
    def __init__(self):
        self.status_from = None
        self.body_from = None

    def extract_status(self, method_details):
        self.status_from = method_details
        return "200"

    def extract_body(self, method_details, resolver):
        self.body_from = (method_details, resolver)
        return {"ok": True}

    def to_text(self):
        return ["EXP"]


class FakePostconditionsBlock:
    def __init__(self):
        self.called_with = None

    def fill_postconditions_block(self, path, method, path_item, resolver):
        self.called_with = (path, method, path_item, resolver)

    def to_text(self):
        return ["POST"]


def test_to_text_assembles_all_blocks_in_order(monkeypatch):
    # Подменяем блоки внутри модуля TestCase
    monkeypatch.setattr(tc_mod, "NameBlock", FakeNameBlock)
    monkeypatch.setattr(tc_mod, "EnvironmentBlock", FakeEnvironmentBlock)
    monkeypatch.setattr(tc_mod, "PreconditionsBlock", FakePreconditionsBlock)
    monkeypatch.setattr(tc_mod, "TestStepsBlock", FakeTestStepsBlock)
    monkeypatch.setattr(tc_mod, "ExpectedResultBlock", FakeExpectedResultBlock)
    monkeypatch.setattr(tc_mod, "PostconditionsBlock", FakePostconditionsBlock)

    # Сконструируем TestCase напрямую из заглушек
    tc = tc_mod.TestCase(
        name_block=FakeNameBlock(),
        environment_block=FakeEnvironmentBlock(),
        expected_result_block=FakeExpectedResultBlock(),
        test_step_block=FakeTestStepsBlock(),
        preconditions_block=FakePreconditionsBlock(),
        postconditions_block=FakePostconditionsBlock(),
    )

    text = tc.to_text()
    lines = text.splitlines()

    # Первая строка — разделитель из 90 дефисов
    assert lines[0] == tc_mod.SEPARATOR_LINE
    # Порядок блоков
    body = "\n".join(lines[1:])
    order = ["NB", "EB", "PRE", "STEP", "EXP", "POST"]
    pos = [body.find(tag) for tag in order]
    assert all(p >= 0 for p in pos), f"Не все теги найдены: {pos}"
    # Убедимся, что порядок последовательный
    assert pos == sorted(pos), f"Неверный порядок блоков: {pos}"


def test_generate_test_cases_builds_cases_and_calls_blocks(monkeypatch):

    monkeypatch.setattr(tc_mod, "NameBlock", FakeNameBlock)
    monkeypatch.setattr(tc_mod, "EnvironmentBlock", FakeEnvironmentBlock)
    monkeypatch.setattr(tc_mod, "PreconditionsBlock", FakePreconditionsBlock)
    monkeypatch.setattr(tc_mod, "TestStepsBlock", FakeTestStepsBlock)
    monkeypatch.setattr(tc_mod, "ExpectedResultBlock", FakeExpectedResultBlock)
    monkeypatch.setattr(tc_mod, "PostconditionsBlock", FakePostconditionsBlock)

    fake_resolver = FakeResolver()

    monkeypatch.setattr(tc_mod, "reference_resolver", fake_resolver, raising=True)

    # Спецификация с одним путем и тремя методами — должно получиться 3 кейса
    spec = {
        "servers": [{"url": "http://api"}],
        "paths": {
            "/items": {
                "get": {"description": "desc-get"},
                "post": {"description": "desc-post"},
                "delete": {"description": "desc-del"},
            }
        }
    }

    cases = tc_mod.TestCase.generate_test_cases(spec)
    assert len(cases) == 3


    assert fake_resolver.initialized_with is spec


    seen_methods = set()
    for case in cases:

        assert isinstance(case.name_block, FakeNameBlock)
        assert isinstance(case.environment_block, FakeEnvironmentBlock)
        assert isinstance(case.preconditions_block, FakePreconditionsBlock)
        assert isinstance(case.test_step_block, FakeTestStepsBlock)
        assert isinstance(case.expected_result_block, FakeExpectedResultBlock)
        assert isinstance(case.postconditions_block, FakePostconditionsBlock)

        # Имя  корректно (метод/путь)
        path, method = case.name_block.name_from
        assert path == "/items"
        assert method in ("get", "post", "delete")
        seen_methods.add(method)

        # Описание извлечено
        assert case.name_block.description in ("desc-get", "desc-post", "desc-del")

        # Серверы извлечены
        assert case.environment_block.servers == ["http://api"]

        # Блоки получили правильные аргументы
        # Preconditions, Postconditions и TestStepBlock
        path_item = spec["paths"]["/items"]
        assert case.preconditions_block.called_with[0] == "/items"
        assert case.preconditions_block.called_with[1] == method
        assert case.preconditions_block.called_with[2] is path_item

        assert case.postconditions_block.called_with[0] == "/items"
        assert case.postconditions_block.called_with[1] == method
        assert case.postconditions_block.called_with[2] is path_item

        # TestStepBlock получил method_details именно для конкретного метода
        recv = case.test_step_block.called_with
        assert recv[0] == "/items"
        assert recv[1] == method
        assert recv[2] is path_item
        assert recv[3] is path_item[method]
        assert recv[4] is fake_resolver

        #  вызваны оба метода
        assert case.expected_result_block.status_from is path_item[method]
        body_method_details, body_resolver = case.expected_result_block.body_from
        assert body_method_details is path_item[method]
        assert body_resolver is fake_resolver


        text = case.to_text()
        assert "NB" in text and "EB" in text and "PRE" in text and "STEP" in text and "EXP" in text and "POST" in text


    assert seen_methods == {"get", "post", "delete"}


def test_generate_test_cases_skips_non_dict_path_items(monkeypatch):

    monkeypatch.setattr(tc_mod, "NameBlock", FakeNameBlock)
    monkeypatch.setattr(tc_mod, "EnvironmentBlock", FakeEnvironmentBlock)
    monkeypatch.setattr(tc_mod, "PreconditionsBlock", FakePreconditionsBlock)
    monkeypatch.setattr(tc_mod, "TestStepsBlock", FakeTestStepsBlock)
    monkeypatch.setattr(tc_mod, "ExpectedResultBlock", FakeExpectedResultBlock)
    monkeypatch.setattr(tc_mod, "PostconditionsBlock", FakePostconditionsBlock)
    monkeypatch.setattr(tc_mod, "reference_resolver", FakeResolver(), raising=True)

    # path_item не dict → должен быть пропущен
    spec = {
        "paths": {
            "/bad": ["not-a-dict"],
        }
    }
    cases = tc_mod.TestCase.generate_test_cases(spec)
    assert cases == []
