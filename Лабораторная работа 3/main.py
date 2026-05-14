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

# схемы
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

# получение данных с цб
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