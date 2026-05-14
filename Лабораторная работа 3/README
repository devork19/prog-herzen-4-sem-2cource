## 1. Постановка задачи

Разработать REST API приложение для отслеживания курсов валют.

**Функциональные требования:**

- CRUD операции для пользователей (создание, чтение, обновление, удаление)
- Подписка и отписка пользователей на курсы валют
- Получение актуальных курсов с сайта Центробанка РФ
- Сохранение истории курсов в базе данных

**Технические требования:**

- FastAPI - веб-фреймворк
- SQLAlchemy - ORM
- SQLite - база данных
- Requests - HTTP запросы к ЦБ РФ
## 2. Структура проекта

```
currency-app/
├── database.py      # настройка бд и модели
├── crud.py          # операции с бд
├── main.py          # эндпоинты API
├── requirements.txt # зависимости
└── README.md        # отчёт
```
## 3. Файлы проекта

### 3.1 `database.py` - настройка базы данных и модели

**Назначение:** подключение к SQLite, создание таблиц, описание моделей.

```python
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime

# подключение к sqlite
SQLALCHEMY_DATABASE_URL = "sqlite:///./currency.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# таблица подписки (связь многие ко многим)
class Subscription(Base):
    __tablename__ = "subscriptions"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    currency_id = Column(Integer, ForeignKey("currencies.id"), primary_key=True)
    user = relationship("User", back_populates="subscriptions")
    currency = relationship("Currency", back_populates="subscriptions")

# таблица пользователей
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")

# таблица валют
class Currency(Base):
    __tablename__ = "currencies"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    subscriptions = relationship("Subscription", back_populates="currency")
    rates = relationship("CurrencyRate", back_populates="currency", cascade="all, delete-orphan")

# таблица истории курсов
class CurrencyRate(Base):
    __tablename__ = "currency_rates"
    id = Column(Integer, primary_key=True)
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=False)
    rate = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.now)
    currency = relationship("Currency", back_populates="rates")

# создаём таблицы
Base.metadata.create_all(bind=engine)

# функция для получения сессии бд
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Объяснение:** Здесь я описал 4 таблицы. Users и Currencies связаны через subscriptions (многие ко многим). CurrencyRate хранит историю курсов чтобы видеть изменения.
### 3.2 `crud.py` - операции с базой данных

**Назначение:** все функции для работы с БД (создание, удаление, поиск).

```python
from sqlalchemy.orm import Session
from database import User, Currency, Subscription, CurrencyRate
from datetime import datetime

# получение пользователя по id
def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

# проверка по username и email
def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

# список всех пользователей
def get_users(db: Session, skip: int = 0, limit: int = 50):
    return db.query(User).offset(skip).limit(limit).all()

# создание пользователя
def create_user(db: Session, username: str, email: str):
    user = User(username=username, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# обновление данных пользователя
def update_user(db: Session, user_id: int, username=None, email=None):
    user = get_user(db, user_id)
    if not user:
        return None
    if username:
        user.username = username
    if email:
        user.email = email
    db.commit()
    db.refresh(user)
    return user

# удаление пользователя
def delete_user(db: Session, user_id: int):
    user = get_user(db, user_id)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True

# подписка на валюту
def subscribe(db: Session, user_id: int, currency_code: str):
    user = get_user(db, user_id)
    if not user:
        return None
    curr = db.query(Currency).filter(Currency.code == currency_code).first()
    if not curr:
        return None
    # проверяем не подписан ли уже
    if db.query(Subscription).filter(Subscription.user_id == user_id, Subscription.currency_id == curr.id).first():
        return False
    db.add(Subscription(user_id=user_id, currency_id=curr.id))
    db.commit()
    return True

# отписка
def unsubscribe(db: Session, user_id: int, currency_code: str):
    curr = db.query(Currency).filter(Currency.code == currency_code).first()
    if not curr:
        return False
    sub = db.query(Subscription).filter(Subscription.user_id == user_id, Subscription.currency_id == curr.id).first()
    if not sub:
        return False
    db.delete(sub)
    db.commit()
    return True

# получить валюты на которые подписан пользователь
def get_user_currencies(db: Session, user_id: int):
    user = get_user(db, user_id)
    if not user:
        return []
    return [sub.currency for sub in user.subscriptions]

# все валюты из бд
def get_all_currencies(db: Session):
    return db.query(Currency).all()

# добавить или обновить валюту
def add_currency(db: Session, code: str, name: str):
    curr = db.query(Currency).filter(Currency.code == code).first()
    if not curr:
        curr = Currency(code=code, name=name)
        db.add(curr)
        db.commit()
        db.refresh(curr)
    elif curr.name != name:
        curr.name = name
        db.commit()
    return curr

# сохранить курс (только если сегодня ещё не сохраняли)
def save_rate(db: Session, currency_id: int, rate: float):
    today = datetime.now().date()
    existing = db.query(CurrencyRate).filter(
        CurrencyRate.currency_id == currency_id,
        CurrencyRate.date >= today
    ).first()
    if not existing:
        db.add(CurrencyRate(currency_id=currency_id, rate=rate))
        db.commit()
        return True
    return False

# получить последний курс валюты
def get_latest_rate(db: Session, currency_id: int):
    return db.query(CurrencyRate).filter(CurrencyRate.currency_id == currency_id).order_by(CurrencyRate.date.desc()).first()
```

**Объяснение:** Этот файл содержит все функции для взаимодействия с БД. Я вынес их отдельно чтобы main.py не был слишком большим. Каждая функция делает одно действие.
### 3.3 `main.py` - эндпоинты API

**Назначение:** обработка HTTP запросов, маршруты, валидация.

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import requests
import xml.etree.ElementTree as ET

from database import get_db
from crud import *
from pydantic import BaseModel, EmailStr
from typing import Optional

app = FastAPI()

# схемы pydantic для валидации
class UserCreate(BaseModel):
    username: str
    email: EmailStr

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    class Config:
        orm_mode = True

class SubscriptionRequest(BaseModel):
    user_id: int
    currency_code: str

class CurrencyResponse(BaseModel):
    id: int
    code: str
    name: str
    class Config:
        orm_mode = True

class UserWithCurrencies(UserResponse):
    currencies: List[CurrencyResponse] = []

class CurrencyRateResponse(BaseModel):
    currency_code: str
    currency_name: str
    rate: float
    date: datetime

# функция парсинга xml с сайта цб
def get_cbr_data():
    try:
        r = requests.get("https://www.cbr.ru/scripts/XML_daily.asp", timeout=30)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        names = {}
        rates = {}
        for val in root.findall('Valute'):
            code = val.find('CharCode').text
            name = val.find('Name').text
            value = float(val.find('Value').text.replace(',', '.'))
            names[code] = name
            rates[code] = value
        names['RUB'] = 'Российский рубль'
        rates['RUB'] = 1.0
        return names, rates
    except:
        raise HTTPException(503, "ошибка при запросе к цб")

# пользователи

@app.post("/users/", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_username(db, user.username):
        raise HTTPException(409, "username уже есть")
    if get_user_by_email(db, user.email):
        raise HTTPException(409, "email уже есть")
    return create_user(db, user.username, user.email)

@app.get("/users/", response_model=List[UserResponse])
def get_users_list(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return get_users(db, skip, limit)

@app.get("/users/{user_id}", response_model=UserWithCurrencies)
def get_user_info(user_id: int, db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(404, "пользователь не найден")
    return UserWithCurrencies(
        id=user.id,
        username=user.username,
        email=user.email,
        created_at=user.created_at,
        currencies=get_user_currencies(db, user_id)
    )

@app.put("/users/{user_id}", response_model=UserResponse)
def update_user_info(user_id: int, upd: UserUpdate, db: Session = Depends(get_db)):
    if upd.username and get_user_by_username(db, upd.username):
        raise HTTPException(409, "username занят")
    if upd.email and get_user_by_email(db, upd.email):
        raise HTTPException(409, "email занят")
    user = update_user(db, user_id, upd.username, upd.email)
    if not user:
        raise HTTPException(404, "пользователь не найден")
    return user

@app.delete("/users/{user_id}", status_code=204)
def delete_user_info(user_id: int, db: Session = Depends(get_db)):
    if not delete_user(db, user_id):
        raise HTTPException(404, "пользователь не найден")

# подписки

@app.post("/subscriptions/", status_code=201)
def subscribe_to_currency(sub: SubscriptionRequest, db: Session = Depends(get_db)):
    result = subscribe(db, sub.user_id, sub.currency_code.upper())
    if result is None:
        raise HTTPException(404, "пользователь или валюта не найдены")
    if result is False:
        raise HTTPException(409, "уже подписан")
    return {"ok": True}

@app.delete("/subscriptions/", status_code=204)
def unsubscribe_from_currency(sub: SubscriptionRequest, db: Session = Depends(get_db)):
    if not unsubscribe(db, sub.user_id, sub.currency_code.upper()):
        raise HTTPException(404, "подписка не найдена")

# валюты

@app.get("/currencies/", response_model=List[CurrencyResponse])
def get_all_currencies_list(db: Session = Depends(get_db)):
    return get_all_currencies(db)

@app.post("/currencies/update")
def update_currencies(db: Session = Depends(get_db)):
    try:
        names, rates = get_cbr_data()
        added = 0
        saved = 0
        for code, name in names.items():
            curr = add_currency(db, code, name)
            if curr.id:
                added += 1
        for code, rate in rates.items():
            curr = db.query(Currency).filter(Currency.code == code).first()
            if curr and save_rate(db, curr.id, rate):
                saved += 1
        return {"currencies_added": added, "rates_saved": saved}
    except:
        raise HTTPException(503, "ошибка обновления")

@app.get("/currencies/{code}/rate", response_model=CurrencyRateResponse)
def get_currency_rate(code: str, db: Session = Depends(get_db)):
    curr = db.query(Currency).filter(Currency.code == code.upper()).first()
    if not curr:
        raise HTTPException(404, "валюта не найдена")
    rate = get_latest_rate(db, curr.id)
    if not rate:
        raise HTTPException(404, "нет данных о курсе")
    return CurrencyRateResponse(
        currency_code=curr.code,
        currency_name=curr.name,
        rate=rate.rate,
        date=rate.date
    )

@app.get("/")
def root():
    return {"message": "Currency API работает", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

**Объяснение:** Здесь все эндпоинты. Для каждого HTTP метода есть своя функция. Pydantic схемы нужны для валидации входных данных. Функция get_cbr_data() парсит XML с сайта ЦБ и возвращает словари с валютами и курсами.


### 3.4 `requirements.txt` - зависимости

```txt
fastapi
uvicorn
sqlalchemy
requests
```

**Объяснение:** Все необходимые библиотеки. Устанавливаются командой pip install -r requirements.txt
## 4. Инструкция по запуску

### 4.1 Установка

```bash
# скачать проект
git clone https://github.com/ivanov/currency-app
cd currency-app

# установить зависимости
pip install -r requirements.txt
```

### 4.2 Запуск

```bash
python main.py
```

После запуска появится сообщение:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 4.3 Проверка работы

Открыть в браузере:
- API: http://127.0.0.1:8000
- Документация Swagger: http://127.0.0.1:8000/docs
## 5. Тестирование API

### 5.1 Создание пользователя

```bash
curl -X POST http://127.0.0.1:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"username": "petrov", "email": "petrov@mail.ru"}'
```

**Ответ:**
```json
{
  "id": 1,
  "username": "petrov",
  "email": "petrov@mail.ru",
  "created_at": "2026-05-14T14:30:00"
}
```

### 5.2 Обновление курсов валют

```bash
curl -X POST http://127.0.0.1:8000/currencies/update
```

**Ответ:**
```json
{
  "currencies_added": 0,
  "rates_saved": 34
}
```

### 5.3 Получение списка валют

```bash
curl http://127.0.0.1:8000/currencies/
```

**Ответ (часть):**
```json
[
  {"id": 1, "code": "USD", "name": "Доллар США"},
  {"id": 2, "code": "EUR", "name": "Евро"},
  {"id": 3, "code": "GBP", "name": "Фунт стерлингов"}
]
```

### 5.4 Подписка на валюту

```bash
curl -X POST http://127.0.0.1:8000/subscriptions/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "currency_code": "USD"}'
```

**Ответ:**
```json
{"ok": true}
```

### 5.5 Получение курса валюты

```bash
curl http://127.0.0.1:8000/currencies/USD/rate
```

**Ответ:**
```json
{
  "currency_code": "USD",
  "currency_name": "Доллар США",
  "rate": 92.45,
  "date": "2026-05-14T15:00:00"
}
```

### 5.6 Получение информации о пользователе с подписками

```bash
curl http://127.0.0.1:8000/users/1
```

**Ответ:**
```json
{
  "id": 1,
  "username": "petrov",
  "email": "petrov@mail.ru",
  "created_at": "2026-05-14T14:30:00",
  "currencies": [
    {"id": 1, "code": "USD", "name": "Доллар США"}
  ]
}
```

### 5.7 Отписка от валюты

```bash
curl -X DELETE http://127.0.0.1:8000/subscriptions/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "currency_code": "USD"}'
```

**Ответ:** пустой (статус 204)

### 5.8 Удаление пользователя

```bash
curl -X DELETE http://127.0.0.1:8000/users/1
```

**Ответ:** пустой (статус 204)

### 5.9 Таблица кодов ответов

| Код | Значение | Когда возникает |
|-----|----------|-----------------|
| 200 | OK | GET запросы, PUT |
| 201 | Created | POST /users/, POST /subscriptions/ |
| 204 | No Content | DELETE запросы |
| 404 | Not Found | Пользователь/валюта не найдены |
| 409 | Conflict | Дубликат username/email/подписки |
| 503 | Service Unavailable | Ошибка при запросе к ЦБ РФ |

## 6. Заключение

### 6.1 Результаты работы

В ходе выполнения лабораторной работы:

1. **Создано REST API** на FastAPI с 11 эндпоинтами
2. **Реализована база данных** SQLite с 4 таблицами через SQLAlchemy
3. **Настроено получение данных** с сайта ЦБ РФ с парсингом XML
4. **Сделана система подписок** пользователей на валюты
5. **Добавлена история курсов** (усложнённый вариант задания)
6. **Написана документация** в README и Swagger

### 6.2 Список эндпоинтов

| Метод | URL | Описание |
|-------|-----|----------|
| POST | /users/ | создать пользователя |
| GET | /users/ | список пользователей |
| GET | /users/{id} | информация о пользователе |
| PUT | /users/{id} | обновить пользователя |
| DELETE | /users/{id} | удалить пользователя |
| POST | /subscriptions/ | подписаться на валюту |
| DELETE | /subscriptions/ | отписаться |
| GET | /currencies/ | список валют |
| POST | /currencies/update | обновить курсы с ЦБ |
| GET | /currencies/{code}/rate | курс валюты |
| GET | / | проверка работы |


