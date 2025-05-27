import shutil
import subprocess
from autotest_generation.utils.Constants import GENERATED_DIR
from autotest_generation.utils.TestCaseReader import load_test_cases
from autotest_generation.services.AutotestGenerator import create_test_file

def run_autotests(yaml_file, allure_results):
    test_data = load_test_cases(yaml_file)
    base_url = test_data["environment"]["base_url"]
    test_cases = test_data["test_cases"]

    if GENERATED_DIR.exists():
        shutil.rmtree(GENERATED_DIR)
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    test_file_path = GENERATED_DIR / "test_todos.py"
    create_test_file(test_cases, base_url, test_file_path)
    print(f"Тесты сгенерированы: {test_file_path}")

    cmd = ["pytest", str(GENERATED_DIR), f"--alluredir={allure_results}"]
    print("Запуск:", " ".join(cmd))
    completed = subprocess.run(cmd, capture_output=True, text=True)
    print("Pytest завершён с кодом:", completed.returncode)
    print(">>> stdout:\n", completed.stdout)
    print(">>> stderr:\n", completed.stderr)
    if completed.returncode == 0:
        print("Тесты прошли успешно!")
    else:
        print("Тесты завершились с ошибками.")
