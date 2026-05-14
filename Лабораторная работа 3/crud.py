from sqlalchemy.orm import Session
from database import User, Currency, Subscription, CurrencyRate
from datetime import datetime

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 50):
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, username: str, email: str):
    user = User(username=username, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

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

def delete_user(db: Session, user_id: int):
    user = get_user(db, user_id)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True

def subscribe(db: Session, user_id: int, currency_code: str):
    user = get_user(db, user_id)
    if not user:
        return None
    curr = db.query(Currency).filter(Currency.code == currency_code).first()
    if not curr:
        return None
    if db.query(Subscription).filter(Subscription.user_id == user_id, Subscription.currency_id == curr.id).first():
        return False
    db.add(Subscription(user_id=user_id, currency_id=curr.id))
    db.commit()
    return True

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

def get_user_currencies(db: Session, user_id: int):
    user = get_user(db, user_id)
    if not user:
        return []
    return [sub.currency for sub in user.subscriptions]

def get_all_currencies(db: Session):
    return db.query(Currency).all()

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

def get_latest_rate(db: Session, currency_id: int):
    return db.query(CurrencyRate).filter(CurrencyRate.currency_id == currency_id).order_by(CurrencyRate.date.desc()).first()