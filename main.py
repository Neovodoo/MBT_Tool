import argparse
from typing import Optional, List
from utils.SpecConverter import OpenAPISpecConverter
from utils.Writer import Writer
from models.TestCase import TestCase



def _cmd_generate(args: argparse.Namespace) -> int:
    spec = OpenAPISpecConverter.convert_spec_to_dict(args.spec)
    test_cases = TestCase.generate_test_cases(spec)
    writer = Writer(test_cases)
    writer.write(args.output)
    print(f"Готово: сгенерировано {len(test_cases)} кейсов → {args.output}")
    return 0

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mbt-openapi", description="Прототип UML-архитектуры: генерация текстовых кейсов из OpenAPI")
    sub = p.add_subparsers(dest="command", required=True)
    p_gen = sub.add_parser("generate", help="Сгенерировать текстовые кейсы из OpenAPI 3.x YAML/JSON")
    p_gen.add_argument("spec", help="Путь к OpenAPI спецификации")
    p_gen.add_argument("-o", "--output", default="cases.txt", help="Путь к выходному TXT")
    p_gen.set_defaults(func=_cmd_generate)
    return p

def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    import sys
    sys.exit(main())