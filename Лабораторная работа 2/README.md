### Лабораторная работа 2

## Формулировка задания

Реализовать паттерн проектирования **«Декоратор»** для получения и конвертации курсов валют Центрального Банка РФ.

**Требования:**

1. Реализовать базовый компонент для получения курсов валют в формате JSON через API ЦБ РФ (использовать сервис `cbr-xml-daily.ru`).
2. Реализовать конкретные декораторы для преобразования результатов в:
    - **YAML-формат** (библиотека `PyYAML`)
    - **CSV-формат** (встроенная библиотека `csv`)
3. Классы-декораторы должны иметь:
    - Основной метод `operation()`, возвращающий объект в соответствующем формате
    - Метод `save(path)`, сохраняющий данные в файл соответствующего типа
4. Реализовать интерфейс с использованием `ABC` и `@abstractmethod`.
5. Соблюдать требования **DAST**:
    - **D**ocstrings (PEP-257)
    - **A**nnotations (PEP-484)
    - **S**pecification (PEP-8)
    - **T**ests (2 теста для каждого компонента)
## Описание работы кода

### `Component(ABC)`

**Назначение:** Абстрактный базовый класс, определяющий интерфейс для всех компонентов и декораторов.

**Параметры:** Не принимает параметров при инициализации.

**Логика:** Содержит два абстрактных метода `operation()` и `save(path)`, которые обязаны реализовать все наследники. Используется `abc.ABC` и декоратор `@abstractmethod` для принудительной реализации интерфейса.
### `ConcreteComponent(Component)`

**Назначение:** Базовый компонент, получающий курсы валют с API ЦБ РФ.

**Параметры:**

- `url` (str) — адрес эндпоинта API (по умолчанию: `https://www.cbr-xml-daily.ru/daily_json.js`)
- `d` (dict | None) — кэш для полученных данных

**Логика:** Метод `operation()` при первом вызове выполняет HTTP-запрос к API через `requests.get()`, парсит JSON-ответ методом `.json()` и кэширует результат в `self.d`. При повторных вызовах возвращает данные из кэша. Метод `save(path)` сохраняет данные в файл в формате JSON с кодировкой UTF-8.
### `Decorator(Component)`

**Назначение:** Базовый класс-обёртка для реализации паттерна Декоратор.

**Параметры:**

- `c` (Component) — ссылка на оборачиваемый компонент

**Логика:** В конструкторе `__init__` сохраняет переданный компонент. Методы `operation()` и `save()` делегируют вызов внутреннему компоненту через `self.c`. Позволяет динамически строить цепочки декораторов без изменения клиентского кода.
### `ConcreteDecoratorA(Decorator)` — YAML-декоратор

**Назначение:** Преобразует данные о курсах валют в формат YAML.

**Параметры:** Наследует `c` от базового декоратора.

**Логика:** Метод `operation()` получает исходные данные через `self.c.operation()`, создаёт структуру с метаданными (формат, источник, временная метка, базовая валюта, дата), извлекает валюты из ключа `Valute`, сериализует результат в YAML-строку через `yaml.dump()`. Метод `save(path)` добавляет расширение `.yaml` и записывает файл с кодировкой UTF-8.
### `ConcreteDecoratorB(Decorator)` — CSV-декоратор

**Назначение:** Преобразует данные о курсах валют в табличный CSV-формат.

**Параметры:** Наследует `c` от базового декоратора.

**Логика:** Метод `operation()` создаёт буфер `io.StringIO()`, инициализирует `csv.DictWriter` с полями (char_code, numeric_code, name, nominal, value, previous, change, date), для каждой валюты вычисляет процент изменения курса и добавляет символ тренда (▲/▼/•). Метод `save(path)` использует кодировку `utf-8-sig` для корректного открытия в Excel.

## Решение

```python
from abc import ABC, abstractmethod  
import json  
import csv  
import requests  
import yaml  
from datetime import datetime  
  
  
class Component(ABC):  
    @abstractmethod  
    def operation(self):  
        pass  
  
    @abstractmethod  
    def save(self, path):  
        pass  
  
  
class ConcreteComponent(Component):  
    def __init__(self):  
        self.url = "https://www.cbr-xml-daily.ru/daily_json.js"  
        self.d = None  
  
    def operation(self):  
        if self.d == None:  
            r = requests.get(self.url)  
            self.d = r.json()  
        return self.d  
  
    def save(self, path):  
        d = self.operation()  
        f = open(path, "w", encoding="utf-8")  
        json.dump(d, f, ensure_ascii=False, indent=2)  
        f.close()  
        return True  
  
  
class Decorator(Component):  
    def __init__(self, c):  
        self.c = c  
  
    def operation(self):  
        return self.c.operation()  
  
    def save(self, path):  
        return self.c.save(path)  
  
  
class ConcreteDecoratorA(Decorator):  # YAML  
    def operation(self):  
        d = self.c.operation()  
        tmp = {}  
        tmp["meta"] = {}  
        tmp["meta"]["fmt"] = "yaml"  
        tmp["meta"]["src"] = "CBR"  
        tmp["meta"]["ts"] = datetime.now().isoformat()  
        tmp["meta"]["base"] = d.get("base", "RUB")  
        tmp["meta"]["date"] = d.get("date")  
        tmp["rates"] = {}  
        v = d.get("Valute", {})  
        for code, info in v.items():  
            if isinstance(info, dict):  
                tmp["rates"][code] = {  
                    "code": info.get("CharCode"),  
                    "name": info.get("Name"),  
                    "value": info.get("Value"),  
                    "prev": info.get("Previous"),  
                    "nom": info.get("Nominal"),  
                }  
        return yaml.dump(tmp, allow_unicode=True, sort_keys=False)  
  
    def save(self, path):  
        if not path.endswith(".yaml") and not path.endswith(".yml"):  
            path = path + ".yaml"  
        content = self.operation()  
        f = open(path, "w", encoding="utf-8")  
        f.write(content)  
        f.close()  
        return True  
  
  
class ConcreteDecoratorB(Decorator):  # CSV  
    def operation(self):  
        import io  
        d = self.c.operation()  
        out = io.StringIO()  
        fields = ["char_code", "numeric_code", "name", "nominal", "value", "previous", "change", "date"]  
        w = csv.DictWriter(out, fieldnames=fields)  
        w.writeheader()  
        date = d.get("date", "")  
        valutes = d.get("Valute", {})  
        for info in valutes.values():  
            if not isinstance(info, dict):  
                continue  
            cur = info.get("Value", 0)  
            prev = info.get("Previous", 0)  
            if prev == 0:  
                chg = "0.00%"  
            else:  
                pct = ((cur - prev) / prev) * 100  
                sym = "▲" if pct > 0 else "▼" if pct < 0 else "•"  
                chg = f"{sym} {abs(pct):.2f}%"  
            row = {  
                "char_code": info.get("CharCode", ""),  
                "numeric_code": info.get("NumCode", ""),  
                "name": info.get("Name", ""),  
                "nominal": info.get("Nominal", 1),  
                "value": cur,  
                "previous": prev,  
                "change": chg,  
                "date": date,  
            }  
            w.writerow(row)  
        return out.getvalue()  
  
    def save(self, path):  
        if not path.endswith(".csv"):  
            path = path + ".csv"  
        content = self.operation()  
        f = open(path, "w", encoding="utf-8-sig", newline="")  
        f.write(content)  
        f.close()  
        return True

```

## Проверка

Тесты реализованы с использованием модуля `unittest.mock` для изоляции от сетевого API. Каждый компонент покрыт двумя тестами: проверка формата вывода и проверка сохранения в файл.

**Моковые данные:** `MOCK_DATA` — фиксированный словарь, имитирующий ответ API ЦБ РФ с валютами USD и EUR.

**Основные тест-кейсы:**

- `test_base_component_returns_dict`: проверка возврата словаря с ключом "Valute" и наличия валют.
- `test_base_component_json_output`: проверка валидности JSON-сериализации.
- `test_yaml_decorator_output`: проверка наличия секций "meta" и "rates" в YAML.
- `test_yaml_decorator_save`: проверка создания файла и его валидности.
- `test_csv_decorator_output`: проверка наличия заголовка и строк с валютами.
- `test_csv_decorator_save`: проверка создания CSV-файла и корректности данных.

---

## Тесты

```python
import json  
import csv  
import os  
import tempfile  
import yaml  
from laba2 import ConcreteComponent, ConcreteDecoratorA, ConcreteDecoratorB  
  
# моковые данные для тестов (чтобы не дергать реальный API каждый раз)  
MOCK_DATA = {  
    "Date": "2024-01-15T00:00:00+03:00",  
    "date": "2024-01-15",  
    "base": "RUB",  
    "Valute": {  
        "USD": {  
            "ID": "R01235",  
            "NumCode": "840",  
            "CharCode": "USD",  
            "Nominal": 1,  
            "Name": "Доллар США",  
            "Value": 89.50,  
            "Previous": 89.20,  
        },  
        "EUR": {  
            "ID": "R01239",  
            "NumCode": "978",  
            "CharCode": "EUR",  
            "Nominal": 1,  
            "Name": "Евро",  
            "Value": 97.30,  
            "Previous": 97.80,  
        },  
    },  
}  
  
  
def test_base_component_returns_dict():  
    """Тест 1: базовый компонент возвращает dict с валютами"""  
    import unittest.mock as mock  
    with mock.patch("requests.get") as m:  
        resp = mock.Mock()  
        resp.json.return_value = MOCK_DATA  
        resp.raise_for_status = mock.Mock()  
        m.return_value = resp  
  
        cc = ConcreteComponent()  
        d = cc.operation()  
  
        assert isinstance(d, dict)  
        assert "Valute" in d  
        assert "USD" in d["Valute"]  
        print(" test_base_component_returns_dict")  
  
  
def test_base_component_json_output():  
    """Тест 2: базовый компонент выдает валидный JSON"""  
    import unittest.mock as mock  
    with mock.patch("requests.get") as m:  
        resp = mock.Mock()  
        resp.json.return_value = MOCK_DATA  
        resp.raise_for_status = mock.Mock()  
        m.return_value = resp  
  
        cc = ConcreteComponent()  
        s = json.dumps(cc.operation(), ensure_ascii=False)  
  
        parsed = json.loads(s)  
        assert parsed["date"] == "2024-01-15"  
        assert "Valute" in parsed  
        print(" test_base_component_json_output")  
  
  
def test_yaml_decorator_output():  
    """Тест 3: YAML декоратор возвращает валидный YAML"""  
    import unittest.mock as mock  
    with mock.patch("requests.get") as m:  
        resp = mock.Mock()  
        resp.json.return_value = MOCK_DATA  
        resp.raise_for_status = mock.Mock()  
        m.return_value = resp  
  
        base = ConcreteComponent()  
        dec = ConcreteDecoratorA(base)  
        y = dec.operation()  
  
        parsed = yaml.safe_load(y)  
        assert "rates" in parsed  
        assert "meta" in parsed  
        assert parsed["meta"]["fmt"] == "yaml"  
        assert "USD" in parsed["rates"]  
        print(" test_yaml_decorator_output")  
  
  
def test_yaml_decorator_save():  
    """Тест 4: YAML декоратор сохраняет файл"""  
    import unittest.mock as mock  
    with mock.patch("requests.get") as m:  
        resp = mock.Mock()  
        resp.json.return_value = MOCK_DATA  
        resp.raise_for_status = mock.Mock()  
        m.return_value = resp  
  
        base = ConcreteComponent()  
        dec = ConcreteDecoratorA(base)  
  
        with tempfile.TemporaryDirectory() as tmp:  
            fp = os.path.join(tmp, "out.yaml")  
            res = dec.save(fp)  
  
            assert res == True  
            assert os.path.exists(fp)  
            with open(fp, "r", encoding="utf-8") as f:  
                content = yaml.safe_load(f)  
            assert "rates" in content  
        print(" test_yaml_decorator_save")  
  
  
def test_csv_decorator_output():  
    """Тест 5: CSV декоратор возвращает валидный CSV"""  
    import unittest.mock as mock  
    with mock.patch("requests.get") as m:  
        resp = mock.Mock()  
        resp.json.return_value = MOCK_DATA  
        resp.raise_for_status = mock.Mock()  
        m.return_value = resp  
  
        base = ConcreteComponent()  
        dec = ConcreteDecoratorB(base)  
        c = dec.operation()  
  
        lines = c.strip().split("\n")  
        assert len(lines) > 1  
        assert "char_code" in lines[0]  
        assert any("USD" in line for line in lines)  
        print(" test_csv_decorator_output")  
  
  
def test_csv_decorator_save():  
    """Тест 6: CSV декоратор сохраняет файл"""  
    import unittest.mock as mock  
    with mock.patch("requests.get") as m:  
        resp = mock.Mock()  
        resp.json.return_value = MOCK_DATA  
        resp.raise_for_status = mock.Mock()  
        m.return_value = resp  
  
        base = ConcreteComponent()  
        dec = ConcreteDecoratorB(base)  
  
        with tempfile.TemporaryDirectory() as tmp:  
            fp = os.path.join(tmp, "out.csv")  
            res = dec.save(fp)  
  
            assert res == True  
            assert os.path.exists(fp)  
            with open(fp, "r", encoding="utf-8-sig") as f:  
                reader = csv.DictReader(f)  
                rows = list(reader)  
            assert len(rows) >= 1  
            assert any(r["char_code"] == "USD" for r in rows)  
        print(" test_csv_decorator_save")  
  
  
# запуск тестов если файл запустили напрямую  
if __name__ == "__main__":  
    print("Running tests...\n")  
    test_base_component_returns_dict()  
    test_base_component_json_output()  
    test_yaml_decorator_output()  
    test_yaml_decorator_save()  
    test_csv_decorator_output()  
    test_csv_decorator_save()  
    print("\n тесты выполнены")
```
## Информация о студенте
Стажков Данила Александрович, 2 курс
