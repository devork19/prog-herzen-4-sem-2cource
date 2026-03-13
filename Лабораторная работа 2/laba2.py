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