from __future__ import annotations

import datetime as dt
from decimal import Decimal
from getpass import getuser

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from backend.db import add_order_to_db, get_orders_from_db
from backend.models import OrderIn, OrderOut

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


def _fmt_date(date: dt.date, /) -> str:
    return date.strftime("%Y-%m-%d (%a)")


def _fmt_datetime(date: dt.datetime, /) -> str:
    return date.strftime("%Y-%m-%d (%a) %H:%M:%S")


def _fmt_price(price: Decimal, /) -> str:
    return format(price, ".2f")


templates = Jinja2Templates(directory="templates")
templates.env.filters["fmt_date"] = _fmt_date
templates.env.filters["fmt_datetime"] = _fmt_datetime
templates.env.filters["fmt_price"] = _fmt_price


@app.get("/", response_class=HTMLResponse)
async def home(*, request: Request) -> Response:
    now = dt.datetime.now()
    orders = await get_orders(date=now.date())
    name = "index.html"
    context = {
        "request": request,
        "username": getuser(),
        "now": now,
        "orders": orders,
    }
    return templates.TemplateResponse(name=name, context=context)


@app.post("/order")
async def add_order(*, order: OrderIn) -> None:
    add_order_to_db(order)


@app.get("/orders")
async def get_orders(*, date: dt.date | None = None) -> list[OrderOut]:
    return get_orders_from_db(date=date)
