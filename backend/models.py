import datetime as dt
from decimal import Decimal

from pydantic import BaseModel


class OrderIn(BaseModel):
    name: str
    date: dt.date
    description: str
    price: Decimal


class OrderOut(BaseModel):
    user: str
    date: dt.date
    description: str
    price: Decimal
