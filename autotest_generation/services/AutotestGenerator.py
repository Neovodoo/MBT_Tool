import textwrap
from pathlib import Path
import re

def generate_test_code(test_case: dict, base_url: str) -> str:
    # Получить имя теста и "очистить" его для использования как идентификатор
    raw_name = test_case.get("Тест-кейс", "unknown_test").replace(" ", "_")
    # Удаляем все символы, кроме букв, цифр и подчёркиваний
    test_name = re.sub(r'[^0-9a-zA-Z_]', '', raw_name)
    # Гарантия, что не начинается с цифры (Python не разрешает)
    if test_name and test_name[0].isdigit():
        test_name = "_" + test_name
    """
    Принимает один тест-кейс (dict) и базовый URL.
    Генерирует код теста (строку), которую можно записать в файл.
    """
    description = test_case.get("Описание", "")
    steps = test_case.get("Шаги", [])
    preconditions = test_case.get("Предусловия", [])
    postconditions = test_case.get("Постусловия", [])
    expected = test_case.get("Ожидаемый результат", {})

    code_lines = []
    # Аннотации Allure
    code_lines.append(f"@allure.title('{test_name}')")
    code_lines.append(f'@allure.description("""{description}""")')
    code_lines.append(f"def test_{test_name}(session, context):")

    # Предусловия
    code_lines.append("    # Предусловия")
    code_lines.append("    with allure.step('Предусловия'):")
    code_lines.append(f"        for pre in {repr(preconditions)}:")
    pre_block = """\
endpoint = pre['Endpoint']
method = endpoint.split()[0]
path = endpoint.split()[1]

headers = pre.get('Headers', {})
cookies = pre.get('Cookies', {})
body = pre.get('Body', {})

# Подстановка плейсхолдеров
path = replace_placeholders(path, context)
body = replace_in_dict(body, context)

# Если тело является словарём, используем параметр json= для автоматической сериализации
if isinstance(body, dict):
    headers.setdefault("Content-Type", "application/json")

url = f"{base_url}{path}"

response = session.request(method, url, headers=headers, cookies=cookies, json=body)
assert response.status_code in [200, 201, 202], f'Неожиданный статус {{response.status_code}} при предусловии'

try:
    resp_json = response.json()
    if isinstance(resp_json, dict) and 'id' in resp_json:
        context['id_todo'] = resp_json['id']
except Exception:
    pass
"""
    code_lines.append(textwrap.indent(textwrap.dedent(pre_block), " " * 12))

    # Основной шаг
    code_lines.append("")
    code_lines.append("    # Основной шаг (Шаги)")
    code_lines.append("    with allure.step('Основной шаг'):")
    code_lines.append(f"        for step in {repr(steps)}:")
    step_block = """\
endpoint = step['Endpoint']
method = endpoint.split()[0]
path = endpoint.split()[1]

headers = step.get('Headers', {})
cookies = step.get('Cookies', {})
body = step.get('Body', {})

# Подстановка плейсхолдеров
path = replace_placeholders(path, context)
body = replace_in_dict(body, context)

if isinstance(body, dict):
    headers.setdefault("Content-Type", "application/json")

url = f"{base_url}{path}"

response = session.request(method, url, headers=headers, cookies=cookies, json=body)
last_response = response
"""
    code_lines.append(textwrap.indent(textwrap.dedent(step_block), " " * 12))

    # Проверка ожидаемого результата
    code_lines.append("")
    code_lines.append("    # Проверка ожидаемого результата")
    code_lines.append("    with allure.step('Проверка ожидаемого результата'):")
    if expected.get("Статус"):
        code_lines.append("        assert str(last_response.status_code) == "
                          f"'{expected.get('Статус')}', 'Ожидался статус {expected.get('Статус')}, получен {{last_response.status_code}}'")
    else:
        code_lines.append("        # Не указан ожидаемый статус, пропускаем проверку")
    if isinstance(expected.get("Body"), list):
        code_lines.append("        resp_json = last_response.json() if last_response.text else []")
        code_lines.append("        assert isinstance(resp_json, list), 'Ожидался список в ответе'")
        code_lines.append(f"        for item in {repr(expected.get('Body'))}:")
        code_lines.append("            assert item in resp_json, f'Не найден ожидаемый объект {item} в ответе'")
    elif isinstance(expected.get("Body"), dict):
        code_lines.append("        resp_json = last_response.json() if last_response.text else {}")
        code_lines.append("        for key, val in " + repr(expected.get("Body")) + ".items():")
        code_lines.append("            assert key in resp_json, f'В ответе нет ключа {key}'")
        code_lines.append("            assert resp_json[key] == val, f'Значение для {key} не совпадает с ожидаемым'")
    else:
        code_lines.append("        # Ожидаемое тело не задано или не поддерживается")

    # Постусловия
    code_lines.append("")
    code_lines.append("    # Постусловия")
    code_lines.append("    with allure.step('Постусловия'):")
    code_lines.append(f"        for post in {repr(postconditions)}:")
    post_block = """\
endpoint = post['Endpoint']
method = endpoint.split()[0]
path = endpoint.split()[1]

headers = post.get('Headers', {})
cookies = post.get('Cookies', {})
body = post.get('Body', {})

path = replace_placeholders(path, context)
body = replace_in_dict(body, context)

if isinstance(body, dict):
    headers.setdefault("Content-Type", "application/json")

url = f"{base_url}{path}"
response = session.request(method, url, headers=headers, cookies=cookies, json=body)
# Обычно cleanup, статус может быть 200/204/404 и т.д.
"""
    code_lines.append(textwrap.indent(textwrap.dedent(post_block), " " * 12))

    return "\n".join(code_lines)

def create_test_file(test_cases: list, base_url: str, generated_file: Path):
    """
    Создаёт .py-файл со всеми тестами, основанными на test_cases.
    Записывает туда фикстуры session() и context(), а также определяет base_url.
    """
    with open(generated_file, "w", encoding="utf-8") as f:
        # Импорты
        f.write("import pytest\n")
        f.write("import allure\n")
        f.write("import requests\n")
        f.write("import json\n\n")
        # Определяем base_url как константу для тестов
        f.write(f"base_url = '{base_url}'\n\n")
        # Фикстуры и вспомогательные функции
        f.write(textwrap.dedent("""\
            @pytest.fixture(scope='session')
            def session():
                s = requests.Session()
                return s

            @pytest.fixture(scope='function')
            def context():
                return {}

            def replace_placeholders(text, context):
                import re
                placeholders = re.findall(r"<(.*?)>", text)
                for ph in placeholders:
                    if ph in context:
                        text = text.replace(f"<{ph}>", str(context[ph]))
                return text

            def replace_in_dict(d, context):
                if not d:
                    return d
                if isinstance(d, dict):
                    new_dict = {}
                    for k, v in d.items():
                        if isinstance(v, str):
                            new_dict[k] = replace_placeholders(v, context)
                        elif isinstance(v, dict):
                            new_dict[k] = replace_in_dict(v, context)
                        elif isinstance(v, list):
                            new_dict[k] = [
                                replace_in_dict(item, context) if isinstance(item, dict)
                                else replace_placeholders(str(item), context) for item in v
                            ]
                        else:
                            new_dict[k] = v
                    return new_dict
                elif isinstance(d, list):
                    return [replace_in_dict(item, context) for item in d]
                else:
                    return replace_placeholders(str(d), context)
        """))
        # Генерируем тестовые функции
        for tc in test_cases:
            code = generate_test_code(tc, base_url)
            f.write("\n\n")
            f.write(code)
            f.write("\n\n")
