from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./currency.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Subscription(Base):
    __tablename__ = "subscriptions"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    currency_id = Column(Integer, ForeignKey("currencies.id"), primary_key=True)
    user = relationship("User", back_populates="subscriptions")
    currency = relationship("Currency", back_populates="subscriptions")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")

class Currency(Base):
    __tablename__ = "currencies"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    subscriptions = relationship("Subscription", back_populates="currency")
    rates = relationship("CurrencyRate", back_populates="currency", cascade="all, delete-orphan")

class CurrencyRate(Base):
    __tablename__ = "currency_rates"
    id = Column(Integer, primary_key=True)
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=False)
    rate = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.now)
    currency = relationship("Currency", back_populates="rates")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()