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

## 👨‍💻 Автор  

MBT Tool — ваш помощник для быстрой автоматизации API тестирования!

Telegram - @NeoVoodoo

---

## 🛠️ Тестовый пример использования 

1. Запустите генерацию контрольных примеров на основе примера спецификации из папки [test_data](test_data)

```bash
python -m test_case_generation.main test_data/test_example_schema.yaml  
```

2. В результате вы получите [текстовый файл](test_data/test_cases_example.txt) с контрольными примерами и [yaml файл](test_data/test_cases_example.yaml) с контрольными примерами

3. Сгенерированные контрольные примеры содержат в себе плейсхолдеры вместо реальных тестовых значений, их необходимо заменить на реальные значения параметров запросов в тестах.\
Например вместо 
```
Endpoint: GET /<number>?json=true
```
необходимо подставить значение: 
```
Endpoint: GET /42?json=true
```
и такую же процедуру необходимо провести для всех плейсхолдеров в контрольных примерах. Полностью исправленая версию файла с контрольными примерами также [находится в репозитории](test_data/corrected_test_cases.yaml)

4. Теперь, после того как yaml файл подготовлен к генерации и запуску автотестов, необходимо запустить команду:
```bash
python -m autotest_generation.main --yaml-file test_data/corrected_test_cases.yaml  --allure-results results
```
5. Для получения подробных результатов выполненых автотестов используйте команду. (Результаты также отображаются в логах консоли) 
```
allure serve allure-results      
```

6. После запуска allure отчета или чтения логов, стало понятно, что в одном из тестов ожидаемый результат не соответствует фактическому, для поля number в ответе приходит не то значение.\
Пример логов консоли:
```
 # Проверка ожидаемого результата
        with allure.step('Проверка ожидаемого результата'):
            assert str(last_response.status_code) == '200', 'Ожидался статус 200, получен {last_response.status_code}'
            resp_json = last_response.json() if last_response.text else {}
            for key, val in {'number': '6/21', 'found': True, 'type': 'date'}.items():
                assert key in resp_json, f'В ответе нет ключа {key}'
>               assert resp_json[key] == val, f'Значение для {key} не совпадает с ожидаемым'
E               AssertionError: Значение для number не совпадает с ожидаемым
E               assert 173 == '6/21'
```
7. При необходимости можно внести изменения в файл с контрольными примерами в ожидаемый результат для третьего контрольного примера. Все элементы контрольных примеров доступны к редактированию в yaml файлах. Также можно добавлять новые контрольные примеры в ручную при необходимости в соответствии с их правилами генерации. Исправленный файл, который полностью соответствует поведению системы находится [тут](test_data/corrected_test_cases_without_mistake.yaml)

---
