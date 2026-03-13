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