import json
import pytest

from models.Step import Step
from models.parameter.Parameter import Parameter



class DummyResolver:
    def resolve_ref(self, node):

        if isinstance(node, str) and node == "#/rb":

            return {"content": {"text/plain": "NOT_A_DICT_MEDIA"}}
        return node


@pytest.fixture
def resolver():
    return DummyResolver()


@pytest.fixture
def param_path():
    return Parameter(name="id", in_="path", required=True, example=1, datatype="integer")


@pytest.fixture
def param_query():
    return Parameter(name="q", in_="query", required=False, example="x", datatype="string")


@pytest.fixture
def param_header():
    return Parameter(name="Auth", in_="header", required=False, example="tok", datatype="string")



def test_extract_data_empty_lists_and_no_body(monkeypatch, resolver):
    monkeypatch.setattr(
        "models.Step.Parameter.extract_data_for_parameters_list",
        lambda path_item, method_details, resolver: [],
        raising=False
    )

    step = Step()
    step.extract_data(path="/users", method="get", path_item={}, method_details={}, resolver=resolver)

    assert step.path == "/users"
    assert step.method == "GET"
    assert step.headers == []
    assert step.path_parameters == []
    assert step.query_parameters == []
    assert step.requestBody is None

    out = "\n".join(step.to_text())
    assert "- Метод: GET" in out
    assert "- URL: /users" in out
    assert "Заголовки отсутствуют" in out
    assert "Параметры пути отсутствуют" in out
    assert "Параметры запроса отсутствуют" in out
    assert "Тело запроса отсутствует" in out


def test_extract_parameters_filled(monkeypatch, resolver, param_path, param_query, param_header):
    # вернём 3 параметра разных типов
    monkeypatch.setattr(
        "models.Step.Parameter.extract_data_for_parameters_list",
        lambda path_item, method_details, resolver: [param_path, param_query, param_header],
        raising=False
    )

    step = Step()
    step.extract_data(path="/items/{id}", method="post", path_item={}, method_details={}, resolver=resolver)

    # фильтрация по in_
    assert [p.name for p in step.path_parameters] == ["id"]
    assert [p.name for p in step.query_parameters] == ["q"]
    assert [p.name for p in step.headers] == ["Auth"]

    out = "\n".join(step.to_text())
    # строки из Parameter.to_line должны присутствовать
    assert "id: Пример:" in out
    assert "q: Пример:" in out
    assert "Auth: Пример:" in out
    # при наличии хотя бы одного элемента ветка "… отсутствуют" не должна появляться
    assert "Заголовки отсутствуют" not in out
    assert "Параметры пути отсутствуют" not in out
    assert "Параметры запроса отсутствуют" not in out


def test_extract_body_with_ref_and_non_dict_media(monkeypatch, resolver):
    # параметры нам не важны здесь
    monkeypatch.setattr(
        "models.Step.Parameter.extract_data_for_parameters_list",
        lambda path_item, method_details, resolver: [],
        raising=False
    )

    method_details = {"requestBody": {"$ref": "#/rb"}}

    step = Step()
    body = step.extract_body(method_details, resolver)
    assert body is None
    assert step.requestBody is None

    out = "\n".join(step.to_text())
    assert "Тело запроса отсутствует" in out


def test_extract_body_json_media_and_schema(monkeypatch, resolver):
    monkeypatch.setattr(
        "models.Step.generate_request_body",
        lambda schema, resolver: {"foo": "bar"},
        raising=False
    )
    monkeypatch.setattr(
        "models.Step.Parameter.extract_data_for_parameters_list",
        lambda path_item, method_details, resolver: [],
        raising=False
    )

    method_details = {
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {"type": "object", "properties": {"foo": {"type": "string"}}, "required": ["foo"]}
                }
            }
        }
    }

    step = Step()
    body = step.extract_body(method_details, resolver)
    assert body == {"foo": "bar"}
    out = "\n".join(step.to_text())
    # Ветка с выводом тела (не должно быть сообщения об отсутствии)
    assert "Тело запроса отсутствует" not in out
    assert json.dumps({"foo": "bar"}, ensure_ascii=False, indent=2).splitlines()[0] in out


def test_to_text_with_additional_info_branch(monkeypatch, resolver):
    monkeypatch.setattr(
        "models.Step.Parameter.extract_data_for_parameters_list",
        lambda path_item, method_details, resolver: [],
        raising=False
    )

    step = Step(path="/x", method="GET", requestBody={"additional_info": {}})
    out = "\n".join(step.to_text())
    assert "Тело запроса отсутствует" in out
