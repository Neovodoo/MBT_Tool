# MBT Tool

**MBT Tool** — инструмент для генерации тест-кейсов из OpenAPI спецификаций и автотестов по YAML-кейсам с поддержкой Allure-отчётов.

---

## 🚀 Быстрый старт

### 1. Клонируйте репозиторий и установите зависимости

```bash
git clone https://github.com/Neovodoo/MBT_Tool.git
cd MBT_tool
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
````

---

### 2. Генерация тест-кейсов из OpenAPI

```bash
python -m test_case_generation.main <путь_к_openapi.yaml>
```

* Появятся файлы с тест-кейсами:

  * `test_cases.txt` — человекочитаемый вариант
  * `test_cases.yaml` — структурированный YAML

#### Пример:

```bash
python -m test_case_generation.main api_pipeline.yml
```

**Опции:**

* `--txt-out <имя_файла>` — имя для текстового вывода
* `--yaml-out <имя_файла>` — имя для yaml
* `--no-print` — не выводить тест-кейсы в консоль

---

### 3. Генерация и запуск автотестов

На вход — сгенерированный `test_cases.yaml`.

```bash
python -m autotest_generation.main --yaml-file test_cases.yaml --allure-results results
```

* Автотесты сгенерируются в папку `generated_tests`
* Запустится pytest с сохранением результатов в папку `results`

**Опции:**

* `--yaml-file` — путь к yaml c тест-кейсами (по умолчанию `test_cases.yaml`)
* `--allure-results` — куда сохранить результаты Allure (по умолчанию `allure-results`)
* `--generated-dir` — папка для сгенерированных тестов (по умолчанию `generated_tests`)

---

### 4. Просмотр Allure-отчёта

Установите Allure Commandline:
[Инструкция по установке Allure](https://docs.qameta.io/allure/#_installing_a_commandline)

Сформируйте и откройте отчёт:

```bash
allure serve results
# или, если путь другой:
allure serve <ваша_папка>
```



## ⚙️ Требования

* Python 3.8+
* pytest
* allure-pytest
* requests
* PyYAML

См. файл [`requirements.txt`](requirements.txt).

---

## ✅ Советы по использованию

* Для нового проекта укажите свой OpenAPI yaml и перегенерируйте тест-кейсы.
* Входные файлы для автотестов (yaml) должны быть **без плейсхолдеров**: только валидные значения в endpoint.
* Папки для автотестов и Allure-отчётов создаются автоматически.
* Можно добавить свои тесты или генерацию под другие спецификации/REST API.
* Используйте этот инструмент для CI/CD, Smoke, Regression тестов и обучения ручных тестировщиков.

---

## 🛠️ Поддержка и развитие

* Форкните проект, предлагайте PR, создавайте issues.
* Все вопросы и предложения — в Issues!

---

## 👨‍💻 Автор  

MBT Tool — ваш помощник для быстрой автоматизации API тестирования!

Telegram - @NeoVoodoo

---
