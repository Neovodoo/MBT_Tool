import json
import re
import uuid
import pytest

from models.test_cases_blocks.EnvironmentBlock import EnvironmentBlock
from models.test_cases_blocks.ExpectedResultBlock import ExpectedResultBlock
from models.test_cases_blocks.NameBlock import NameBlock
from models.test_cases_blocks.PreconditionsBlock import PreconditionsBlock
from models.test_cases_blocks.PostconditionsBlock import PostconditionsBlock
from models.test_cases_blocks.TestStepBlock import TestStepsBlock



class FakeStep:
    """Заглушка Step, совместимая с вызовами в блоках.
    Поддерживает extract_data как с 2 аргументами, так и с 5 (см. TestStepsBlock.fillTestStepBlock)."""
    def __init__(self):
        self.path = ""
        self.method = ""
        self._calls = 0

    def extract_data(self, *args):
        # Вариант 1: (path, method)
        if len(args) == 2:
            path, method = args
        # Вариант 2: (path, method, path_item, method_details, resolver)
        elif len(args) == 5:
            path, method = args[0], args[1]
        else:
            raise AssertionError(f"Unexpected extract_data args: {args}")
        self.path = path
        self.method = str(method).upper()
        self._calls += 1

    def to_text(self):
        return [
            f"- Метод: {self.method}",
            "",
            f"- URL: {self.path}",
        ]


class DummyResolver:
    def __init__(self, mapping=None):
        self.mapping = mapping or {}

    def resolve_ref(self, node):
        # В ExpectedResultBlock.resolve_ref передают dict с "$ref"
        if isinstance(node, dict) and "$ref" in node:
            return self.mapping.get(node["$ref"], node)
        if isinstance(node, str) and node in self.mapping:
            return self.mapping[node]
        return node


@pytest.fixture
def resolver():
    return DummyResolver()



# EnvironmentBlock
def test_environment_block_to_text_with_servers():
    eb = EnvironmentBlock(servers=["https://api.example.com", "http://localhost:8080"])
    out = "\n".join(eb.to_text())
    assert out.splitlines()[0] == "Окружение:"
    assert "- Сервера:" in out
    assert "    - https://api.example.com" in out
    assert "    - http://localhost:8080" in out
    assert re.search(r"-{20}$", out.strip().splitlines()[-1])  # SEPARATOR_LINE


def test_environment_block_to_text_without_servers():
    eb = EnvironmentBlock()
    out = "\n".join(eb.to_text())
    assert "  - -" in out  # ветка пустого списка
    assert re.search(r"-{20}$", out.strip().splitlines()[-1])


def test_environment_block_extract_servers_filters_non_strings():
    spec = {
        "servers": [
            {"url": "https://ok"},
            {"url": 123},
            {"url": None},
            {"url": "http://also-ok"},
            {},
        ]
    }
    eb = EnvironmentBlock()
    servers = eb.extract_servers(spec)
    assert servers == ["https://ok", "http://also-ok"]



# ExpectedResultBlock
def test_expected_result_block_extract_status_priority_and_fallback():
    b = ExpectedResultBlock()
    code = b.extract_status({"responses": {"418": {}, "201": {}, "204": {}}})
    # По списку приоритетов 200..206 — выберется "201", а не "418"
    assert code == "201"
    assert b.expectedResponseStatus == "201"

    b = ExpectedResultBlock()
    code = b.extract_status({"responses": {"418": {}, "301": {}}})
    # Ничего из 200..206 нет — берётся первый ключ
    assert code in {"418", "301"}  # порядок dict может варьироваться в старых Py
    assert b.expectedResponseStatus == code

    b = ExpectedResultBlock()
    code = b.extract_status({"responses": {}})
    assert code is None
    assert b.expectedResponseStatus == ""


def test_expected_result_block_extract_body_with_ref_and_json(monkeypatch, resolver):
    monkeypatch.setattr(
        "models.test_cases_blocks.ExpectedResultBlock.generate_request_body",
        lambda schema, r: {"ok": True},
        raising=False,
    )
    # Ответ под $ref
    resolver.mapping = {
        "#/resp": {
            "content": {
                "application/json": {
                    "schema": {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]}
                }
            }
        }
    }
    details = {"responses": {"200": {"$ref": "#/resp"}}}
    b = ExpectedResultBlock()
    body = b.extract_body(details, resolver)
    assert body == {"ok": True}
    assert b.expectedResponseBody == {"ok": True}

    # to_text печатает JSON, а не «тело отсутствует»
    text = "\n".join(b.to_text())
    assert "Тело ответа отсутствует" not in text
    assert json.dumps({"ok": True}, ensure_ascii=False, indent=2).splitlines()[0] in text


def test_expected_result_block_extract_body_non_dict_media(monkeypatch, resolver):
    # media не dict → тело None
    details = {"responses": {"200": {"content": {"text/plain": "OK"}}}}
    b = ExpectedResultBlock()
    body = b.extract_body(details, resolver)
    assert body is None
    assert b.expectedResponseBody is None

    text = "\n".join(b.to_text())
    assert "Тело ответа отсутствует" in text


def test_expected_result_block_to_text_additional_info_branch():
    b = ExpectedResultBlock(expectedResponseStatus="200", expectedResponseBody={"additional_info": {}})
    text = "\n".join(b.to_text())
    assert "- Статус ответа: 200" in text
    assert "Тело ответа отсутствует" in text


# NameBlock
def test_name_block_generate_uuid_and_name_and_description():
    nb = NameBlock()

    u = nb.generate_uuid()
    assert isinstance(u, str) and len(u) >= 8
    # Формат UUID
    uuid.UUID(u)

    # Имя
    name = nb.generate_name("/users", "get")
    assert name == "Проверка метода <get> для пути </users>"

    # Описание: заданное
    desc = nb.extract_description({"description": "hello"})
    assert desc == "hello"

    # Описание: по умолчанию
    nb2 = NameBlock()
    nb2.extract_description({})
    assert nb2.description == "Описание отсутствует"

    # to_text формат
    out = "\n".join(nb.to_text())
    assert "Контрольный пример:" in out
    assert "Уникальный идентификатор:" in out
    assert "Описание:" in out
    assert re.search(r"-{20}$", out.strip().splitlines()[-1])



# Preconditions / Postconditions Blocks
def test_preconditions_postconditions_fill_with_fake_steps(monkeypatch, resolver):

    monkeypatch.setattr("models.test_cases_blocks.PreconditionsBlock.Step", FakeStep)
    monkeypatch.setattr("models.test_cases_blocks.PostconditionsBlock.Step", FakeStep)

    # Спецификация пути: есть POST и DELETE
    path_item = {
        "post": {"x": 1},
        "delete": {"y": 2},
    }

    pre = PreconditionsBlock()
    pre.fill_preconditions_block("/p", "GET", path_item, resolver)
    assert len(pre.steps) == 1
    assert pre.steps[0].method == "POST"
    assert pre.steps[0].path == "/p"

    post = PostconditionsBlock()
    post.fill_postconditions_block("/p", "PUT", path_item, resolver)
    assert len(post.steps) == 1
    assert post.steps[0].method == "DELETE"
    assert post.steps[0].path == "/p"

    # Если тестируемый метод не GET/PUT — ничего не добавляется
    pre2 = PreconditionsBlock()
    pre2.fill_preconditions_block("/p", "POST", path_item, resolver)
    assert pre2.steps == []

    post2 = PostconditionsBlock()
    post2.fill_postconditions_block("/p", "POST", path_item, resolver)
    assert post2.steps == []


    assert "Предусловия:" in "\n".join(pre.to_text())
    assert "Постусловия:" in "\n".join(post.to_text())

    empty_out = "\n".join(pre2.to_text())
    assert "Предусловия отсутствуют" in empty_out
    empty_out = "\n".join(post2.to_text())
    assert "Постусловия отсутствуют" in empty_out



# TestStepsBlock
def test_teststepsblock_create_and_update_step(monkeypatch, resolver):
    # Подменим Step на FakeStep, который принимает 2 или 5 аргументов в extract_data
    monkeypatch.setattr("models.test_cases_blocks.TestStepBlock.Step", FakeStep)

    block = TestStepsBlock()


    created = block.fillTestStepBlock("/x", "post", {"dummy": 1}, {"dummy": 2}, resolver)
    assert isinstance(created, FakeStep)
    assert created.method == "POST"
    assert created.path == "/x"
    assert len(block.steps) == 1
    # to_text с шагами
    out = "\n".join(block.to_text())
    assert "Шаг 1:" in out
    assert "- Метод: POST" in out

    # Обновление существующего шага (ветка if, вызов extract_data с двумя аргументами)
    updated = block.fillTestStepBlock("/x", "POST", {"ignored": True}, {"ignored": True}, resolver)
    assert updated is created
    assert updated._calls >= 2   # extract_data вызывался дважды (создание и обновление)

    # проверка ветки "Шаги отсутствуют"
    empty_block = TestStepsBlock()
    out_empty = "\n".join(empty_block.to_text())
    assert "Шаги отсутствуют в спецификации" in out_empty
