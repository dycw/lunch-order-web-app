from __future__ import annotations

import datetime as dt

from fastapi.routing import APIRouter

from backend.db import add_order_to_db, get_orders_from_db
from backend.models import OrderIn, OrderOut

router = APIRouter(prefix="/api")


@router.post("/order/")
async def add_order(*, order: OrderIn) -> None:
    add_order_to_db(order)


@router.get("/orders/")
async def get_orders(*, date: dt.date | None = None) -> list[OrderOut]:
    return get_orders_from_db(date=date)
