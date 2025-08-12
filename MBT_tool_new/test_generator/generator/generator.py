def save_test_cases_to_file(test_cases: list, filename: str):
    with open(filename, 'w', encoding='utf-8') as f:
        for test_case in test_cases:
            f.write(test_case.to_text())
            f.write('\n' + '-' * 50 + '\n\n')