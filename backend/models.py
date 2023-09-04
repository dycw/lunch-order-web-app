import datetime as dt
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class OrderIn(BaseModel):
    name: str
    datetime: dt.datetime
    description: str
    price: Decimal


class OrderOut(BaseModel):
    id: UUID  # noqa: A003
    user: str
    datetime: dt.datetime
    description: str
    price: Decimal
