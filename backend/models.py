import datetime as dt
from decimal import Decimal

from pydantic import BaseModel


class OrderIn(BaseModel):
    name: str
    datetime: dt.datetime
    description: str
    price: Decimal


class OrderOut(BaseModel):
    user: str
    datetime: dt.datetime
    description: str
    price: Decimal
