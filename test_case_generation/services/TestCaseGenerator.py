import json
import re
from typing import Dict, Any, List, Optional

import yaml

from test_case_generation.models.OpenAPISpec import OpenAPISpec
from test_case_generation.models.TestCase import TestCase
from test_case_generation.models.Operation import Operation
from test_case_generation.models.SchemaObject import SchemaObject
from test_case_generation.utils.UniversalJSONEncoder import UniversalJSONEncoder

class TestCaseGenerator:
    """
    Генератор тест-кейсов с учётом всех улучшений:
    - форматирование (под-шаги) + оформление + endpoint/summary/description
    - предусловия (POST), постусловия (DELETE)
    - ...
    - сохранение плейсхолдеров <id_...>, типизированных заглушек test_value (::String) и т.д.
    - генерация curl (осталась для текстового вывода), но без неё в YAML.
    """

    def __init__(self, spec: OpenAPISpec):
        self.spec = spec
        self.base_url = spec.get_base_url()
        self.test_cases: List[TestCase] = []

        # Соберём информацию о потенциально "связанных" операциях
        self.resource_map: Dict[str, Dict[str, Operation]] = {}
        self._build_resource_map()

    def _build_resource_map(self):
        for op in self.spec.parsed_operations:
            segments = op.path.strip("/").split("/")
            if len(segments) > 1 and "{" in segments[-1]:
                base_path = "/" + "/".join(segments[:-1])
            else:
                base_path = op.path

            if base_path not in self.resource_map:
                self.resource_map[base_path] = {}
            self.resource_map[base_path][op.method] = op

    def generate_test_cases(self):
        count = 1
        for op in self.spec.parsed_operations:
            name = f"{op.operation_id or op.summary or op.method}_{count}"
            test = self._make_test_case(op, name)
            self.test_cases.append(test)
            count += 1

    def _make_test_case(self, op: Operation, tc_name: str) -> TestCase:
        """
        Формирует объект TestCase, включая:
         - текстовые поля для старого формата (preconditions, steps, expected и т.п.)
         - структурированные поля для YAML (preconditions_struct, steps_struct, postconditions_struct)
        """
        preconditions: List[str] = []
        steps: List[str] = []
        expected: List[str] = []
        postconditions: List[str] = []

        # Сформируем endpoint, смысл и описание
        endpoint_str = f"{op.method} {op.path}"
        summary_str = op.summary.strip() if op.summary else ""
        desc_str = op.description.strip() if op.description else ""

        # 1) Подготовка структур для YAML
        preconditions_struct: List[Dict[str, Any]] = []
        steps_struct: List[Dict[str, Any]] = []
        postconditions_struct: List[Dict[str, Any]] = []
        expected_struct: Dict[str, Any] = {}

        # Обработка path-параметров
        path_param_names = []
        for p in op.parameters:
            if p.get('in') == 'path':
                path_param_names.append(p['name'])

        replaced_path = self._replace_path_params(op.path, path_param_names)
        # Для query/header/cookies
        headers_main = {}
        cookies_main = {}
        query_params_main = {}

        for p in op.parameters:
            p_in = p.get('in')
            p_name = p.get('name')
            if p_in == 'header':
                headers_main[p_name] = self._get_param_example(p)
            elif p_in == 'query':
                query_params_main[p_name] = self._get_param_example(p)
            elif p_in == 'cookie':
                cookies_main[p_name] = self._get_param_example(p)

        query_str = self._build_query_string(query_params_main)
        full_path = replaced_path + query_str

        # request body (для шага)
        req_body_str = self._build_request_body_str(op)
        # resp body + код (для expected)
        resp_body_str, code = self._build_response_body_str(op)

        # ------------------------------------------------
        # Предусловия (если это GET/PUT/DELETE/PATCH, часто нужно POST для создания ресурса)
        # Текстом
        if op.method in ("GET", "PUT", "DELETE", "PATCH"):
            post_op = self._get_related_post_op(op)
            if post_op:
                precond_text = self._build_precondition_text(post_op, replaced_path)
                if precond_text:
                    preconditions.append(precond_text)

                # Для YAML-структуры
                precond_struct = self._build_precondition_struct(post_op)
                if precond_struct:
                    preconditions_struct.append(precond_struct)

        # ------------------------------------------------
        # Постусловия (если операция != DELETE -> удалить ресурс)
        if op.method != "DELETE":
            delete_op = self._get_related_delete_op(op)
            if delete_op:
                postcond_text = self._build_postcondition_text(delete_op, replaced_path)
                if postcond_text:
                    postconditions.append(postcond_text)

                postcond_struct = self._build_postcondition_struct(delete_op)
                if postcond_struct:
                    postconditions_struct.append(postcond_struct)

        # ------------------------------------------------
        # Основной шаг (текст)
        step_text = ""
        if req_body_str.strip():
            step_text = (
                f"Отправить запрос {op.method} {full_path} с телом:\n"
                f"{req_body_str}\n"
            )
        else:
            step_text = f"Отправить запрос {op.method} {full_path} (без тела)\n"

        # headers, cookies
        if cookies_main:
            c_list = [f"{k}={v}" for k, v in cookies_main.items()]
            step_text += f"Установить cookie: {'; '.join(c_list)}\n"
        if headers_main:
            step_text += f"Хедеры: {json.dumps(headers_main, ensure_ascii=False)}\n"

        # добавляем curl в текстовый вывод
        curl_cmd = self._build_curl(op.method, full_path, headers_main, cookies_main, req_body_str)
        step_text += f"curl: {curl_cmd}"
        steps.append(step_text)

        # ------------------------------------------------
        # Основной шаг (структура YAML)
        main_step_struct = {
            "Endpoint": f"{op.method} {replaced_path}{query_str}",
            "Headers": headers_main,
            "Cookies": cookies_main,
            "Body": self._try_json_load(req_body_str) if req_body_str.strip() else {}
        }
        steps_struct.append(main_step_struct)

        # ------------------------------------------------
        # Ожидаемый результат (текст)
        if resp_body_str.strip():
            ex = f"Получен ответ {code} с телом:\n{resp_body_str}"
        else:
            ex = f"Получен ответ {code} (тело отсутствует)"
        expected.append(ex)

        # Ожидаемый результат (структура)
        resp_body_dict = self._try_json_load(resp_body_str) if resp_body_str.strip() else {}
        expected_struct["status"] = code
        expected_struct["body"] = resp_body_dict

        # Собираем объект TestCase
        tc = TestCase(
            name=tc_name,
            preconditions=preconditions,
            steps=steps,
            expected=expected,
            postconditions=postconditions,
            endpoint=endpoint_str,
            operation_summary=summary_str,
            operation_description=desc_str
        )
        # Дополняем его структурные поля (для YAML)
        tc.preconditions_struct = preconditions_struct
        tc.steps_struct = steps_struct
        tc.postconditions_struct = postconditions_struct
        tc.expected_struct = expected_struct

        return tc

    # ======================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ДЛЯ ОФОРМЛЕНИЯ
    # ======================================

    def _build_precondition_text(self, post_op: Operation, replaced_main_path: str) -> str:
        req_body_str = self._build_request_body_str(post_op)
        p = post_op.path
        method = post_op.method
        lines = []
        lines.append(f"Отправить запрос {method} {p} для создания тестового ресурса.")
        if req_body_str.strip():
            lines.append(f"Тело запроса:\n{req_body_str}")
        curl_cmd = self._build_curl(method, p, {}, {}, req_body_str)
        lines.append(f"curl: {curl_cmd}")
        lines.append("Считать ID созданного ресурса (например, <id_resource>) для использования далее.")
        return "\n".join(lines)

    def _build_precondition_struct(self, post_op: Operation) -> Dict[str, Any]:
        """
        Возвращаем структуру предусловия {Endpoint, Headers, Cookies, Body}.
        """
        param_names = self._extract_path_param_names(post_op)
        replaced_path = self._replace_path_params(post_op.path, param_names)

        body_json_str = self._build_request_body_str(post_op)
        body_dict = self._try_json_load(body_json_str) if body_json_str.strip() else {}
        return {
            "Endpoint": f"{post_op.method} {replaced_path}",
            "Headers": {},
            "Cookies": {},
            "Body": body_dict
        }

    def _build_postcondition_text(self, delete_op: Operation, replaced_main_path: str) -> str:
        p_clean = delete_op.path.split("?")[0]
        lines = []
        lines.append(f"Отправить запрос DELETE {p_clean} для удаления тестового ресурса.")
        curl_cmd = self._build_curl("DELETE", p_clean, {}, {}, "")
        lines.append(f"curl: {curl_cmd}")
        return "\n".join(lines)

    def _build_postcondition_struct(self, delete_op: Operation) -> Dict[str, Any]:
        param_names = self._extract_path_param_names(delete_op)
        replaced_path = self._replace_path_params(delete_op.path, param_names)
        return {
            "Endpoint": f"DELETE {replaced_path}",
            "Headers": {},
            "Cookies": {},
            "Body": {}
        }

    # ======================================
    # Поиск "родственных" операций
    # ======================================
    def _get_related_post_op(self, op: Operation) -> Optional[Operation]:
        base_path = self._get_base_path(op.path)
        method_map = self.resource_map.get(base_path, {})
        return method_map.get("POST")

    def _get_related_delete_op(self, op: Operation) -> Optional[Operation]:
        base_path = self._get_base_path(op.path)
        method_map = self.resource_map.get(base_path, {})
        return method_map.get("DELETE")

    # ======================================
    # Прочие вспомогательные методы
    # ======================================
    def _get_base_path(self, full_path: str) -> str:
        segments = full_path.strip("/").split("/")
        if len(segments) > 1 and "{" in segments[-1]:
            return "/" + "/".join(segments[:-1])
        else:
            return full_path

    def _extract_path_param_names(self, op: Operation) -> List[str]:
        result = []
        for p in op.parameters:
            if p.get('in') == 'path':
                result.append(p['name'])
        return result

    def _replace_path_params(self, path: str, path_param_names: List[str]) -> str:
        new_path = path
        matches = re.findall(r"\{([^}]+)\}", path)
        for m in matches:
            if m in path_param_names:
                placeholder = self._make_path_placeholder(m)
                new_path = new_path.replace(f"{{{m}}}", placeholder)
            else:
                new_path = new_path.replace(f"{{{m}}}", f"<{m}>")
        return new_path

    def _make_path_placeholder(self, param_name: str) -> str:
        name_lower = param_name.lower().rstrip('_')
        if name_lower.endswith("id"):
            base = name_lower[:-2].rstrip('_')
            if base:
                return f"<id_{base}>"
            else:
                return "<id>"
        else:
            return f"<{param_name}>"

    def _build_query_string(self, query_params: Dict[str, str]) -> str:
        if not query_params:
            return ''
        from urllib.parse import urlencode
        q = urlencode(query_params)
        return f"?{q}"

    def _get_param_example(self, param: Dict[str, Any]) -> str:
        examples_dict = param.get('examples', {})
        if examples_dict and isinstance(examples_dict, dict):
            first_example = next(iter(examples_dict.values()), None)
            if first_example and isinstance(first_example, dict):
                val = first_example.get('value')
                if val is not None:
                    return str(val)

        schema = param.get('schema', {})
        if 'example' in schema:
            return str(schema['example'])

        enum_vals = schema.get('enum')
        if enum_vals and len(enum_vals) > 0:
            return f"{enum_vals[0]} (enum)"

        st = schema.get('type')
        fm = schema.get('format')
        return self._gen_stub_value(st, fm)

    def _gen_stub_value(self, schema_type: Optional[str], schema_format: Optional[str]) -> str:
        if schema_type == 'string':
            if schema_format == 'date':
                return "test_value (::Date)"
            elif schema_format == 'date-time':
                return "test_value (::DateTime)"
            elif schema_format == 'uuid':
                return "test_value (::UUID)"
            else:
                return "test_value (::String)"
        elif schema_type == 'boolean':
            return "true"
        elif schema_type == 'integer':
            return "12345"
        elif schema_type == 'number':
            return "3.14"
        return "test_value (::Unknown)"

    def _build_request_body_str(self, op: Operation) -> str:
        rb = op.request_body
        if not rb:
            return ""
        c = rb.get('content', {})
        if 'application/json' not in c:
            return ""
        media_info = c['application/json']

        if 'examples' in media_info:
            examples_dict = media_info['examples']
            if isinstance(examples_dict, dict):
                first_ex = next(iter(examples_dict.values()), None)
                if first_ex and isinstance(first_ex, dict):
                    ex_val = first_ex.get('value')
                    if ex_val is not None:
                        return json.dumps(ex_val, ensure_ascii=False, indent=2, cls=UniversalJSONEncoder)

        schema_def = media_info.get('schema')
        if not schema_def:
            return ""
        obj = self._gen_example(schema_def)
        return json.dumps(obj, ensure_ascii=False, indent=2, cls=UniversalJSONEncoder)

    def _build_response_body_str(self, op: Operation) -> (str, str):
        codes = [c for c in op.responses if c.startswith('2')]
        if not codes:
            return ("", "xxx")
        code = sorted(codes)[0]
        resp_info = op.responses[code]
        c = resp_info.get('content', {})
        if 'application/json' not in c:
            return ("", code)
        media_info = c['application/json']

        if 'examples' in media_info:
            examples_dict = media_info['examples']
            if isinstance(examples_dict, dict):
                first_ex = next(iter(examples_dict.values()), None)
                if first_ex and isinstance(first_ex, dict):
                    ex_val = first_ex.get('value')
                    if ex_val is not None:
                        return (json.dumps(ex_val, ensure_ascii=False, indent=2, cls=UniversalJSONEncoder), code)

        schema_def = media_info.get('schema')
        if not schema_def:
            return ("", code)
        obj = self._gen_example(schema_def)
        return (json.dumps(obj, ensure_ascii=False, cls=UniversalJSONEncoder), code)

    def _gen_example(self, schema_def: Dict[str, Any]) -> Any:
        if 'allOf' in schema_def:
            merged = {}
            for sub in schema_def['allOf']:
                sub_obj = self._gen_example(sub)
                if isinstance(sub_obj, dict):
                    merged.update(sub_obj)
            return merged
        if 'oneOf' in schema_def:
            return self._gen_example(schema_def['oneOf'][0])
        if 'anyOf' in schema_def:
            return self._gen_example(schema_def['anyOf'][0])

        ref = schema_def.get('$ref')
        if ref:
            ref_name = ref.split('/')[-1]
            if ref_name in self.spec.parsed_schemas:
                return self._gen_from_schema_obj(self.spec.parsed_schemas[ref_name])
            return "test_value (::UnknownRef)"

        if 'example' in schema_def:
            return schema_def['example']

        enum_vals = schema_def.get('enum')
        if enum_vals and len(enum_vals) > 0:
            return f"{enum_vals[0]} (enum)"

        st = schema_def.get('type')
        fm = schema_def.get('format')

        if st == 'object':
            props = schema_def.get('properties', {})
            result = {}
            for k, v in props.items():
                result[k] = self._gen_example(v)
            return result
        elif st == 'array':
            items = schema_def.get('items', {})
            return [self._gen_example(items)]
        elif st == 'string':
            if fm == 'date':
                return "test_value (::Date)"
            elif fm == 'date-time':
                return "test_value (::DateTime)"
            elif fm == 'uuid':
                return "test_value (::UUID)"
            else:
                return "test_value (::String)"
        elif st == 'boolean':
            return True
        elif st == 'integer':
            return 12345
        elif st == 'number':
            return 3.14
        return "test_value (::Unknown)"

    def _gen_from_schema_obj(self, sobj: SchemaObject) -> Any:
        if sobj.ref:
            ref_name = sobj.ref.split('/')[-1]
            if ref_name in self.spec.parsed_schemas:
                return self._gen_from_schema_obj(self.spec.parsed_schemas[ref_name])
            return "test_value (::UnknownRef)"

        if sobj.example is not None:
            return sobj.example

        if sobj.enum_values:
            return f"{sobj.enum_values[0]} (enum)"

        st = sobj.schema_type
        fm = sobj.schema_format

        if st == 'object':
            out = {}
            for k, prop_sobj in sobj.properties.items():
                out[k] = self._gen_from_schema_obj(prop_sobj)
            return out
        elif st == 'array':
            return ["test_value (::Array)"]
        elif st == 'string':
            if fm == 'date':
                return "test_value (::Date)"
            elif fm == 'date-time':
                return "test_value (::DateTime)"
            elif fm == 'uuid':
                return "test_value (::UUID)"
            else:
                return "test_value (::String)"
        elif st == 'boolean':
            return True
        elif st == 'integer':
            return 12345
        elif st == 'number':
            return 3.14
        return "test_value (::Unknown)"

    def _build_curl(self, method: str, path: str, headers: Dict[str, str], cookies: Dict[str, str], body: str) -> str:
        parts = [f"curl -X {method} '{(self.base_url or '')}{path}'"]
        for k, v in headers.items():
            parts.append(f"  -H '{k}: {v}'")
        if cookies:
            cookie_str = "; ".join([f"{ck}={cv}" for ck, cv in cookies.items()])
            parts.append(f"  -H 'Cookie: {cookie_str}'")
        if body.strip():
            safe_body = body.replace("'", r"'\''")
            parts.append(f"  -d '{safe_body}'")
        return " \\\n".join(parts)

    def _try_json_load(self, s: str) -> Any:
        try:
            return json.loads(s)
        except:
            return {}

    # Методы сохранения/вывода

    def print_test_cases(self) -> None:
        """
        Выводит все тест-кейсы в текстовом (старом) формате в stdout.
        """
        for tc in self.test_cases:
            print(tc)

    def save_test_cases(self, filename: str) -> None:
        """
        Сохраняет тест-кейсы в текстовом формате (старом) в файл.
        """
        with open(filename, 'w', encoding='utf-8') as f:
            for tc in self.test_cases:
                f.write(str(tc))

    def save_test_cases_yaml(self, filename: str) -> None:
        """
        Сохраняет тест-кейсы в файл в формате YAML,
        добавляя блок окружения и две пустые строки между элементами test_cases.
        """
        # 1) Собираем список словарей для каждого тест-кейса
        data_testcases = [tc.to_yaml_dict() for tc in self.test_cases]

        # 2) Формируем блок окружения (environment)
        environment_data = {
            "base_url": self.spec.get_base_url()  # Берём из servers[0].url
        }

        with open(filename, 'w', encoding='utf-8') as f:
            # Сначала пишем блок окружения
            f.write("environment:\n")
            env_dump = yaml.dump(environment_data, sort_keys=False, allow_unicode=True, default_flow_style=False)
            # Сдвинем строчки на 2 пробела (как и test_cases)
            env_lines = env_dump.splitlines()
            env_indented = ["  " + line for line in env_lines]
            # Вставим
            f.write("\n".join(env_indented) + "\n\n")

            # Теперь выводим корневой ключ test_cases
            f.write("test_cases:\n")

            # Обходим тест-кейсы по одному
            for item in data_testcases:
                # Выделяем YAML для одного тест-кейса
                dumped_item = yaml.dump(item, sort_keys=False, allow_unicode=True, default_flow_style=False)

                # Делаем отступ и "- " как в предыдущей версии
                lines = dumped_item.splitlines()
                indented = ["  " + l for l in lines]
                if indented:
                    indented[0] = "- " + indented[0][2:]
                block = "\n".join(indented) + "\n\n\n"
                f.write(block)