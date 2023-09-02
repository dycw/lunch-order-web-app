from __future__ import annotations

import datetime as dt
from decimal import Decimal
from getpass import getuser

from fastapi import FastAPI, Form, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from backend.db import add_order_to_db, get_orders_from_db
from backend.models import OrderIn
from backend.routes.api import router

app = FastAPI()
app.include_router(router=router)
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
    orders = get_orders_from_db(date=now.date())
    name = "index.html"
    context = {
        "request": request,
        "now": now,
        "username": getuser(),
        "orders": orders,
    }
    return templates.TemplateResponse(name=name, context=context)


@app.get("/order")
async def order_now(*, request: Request) -> Response:
    name = "order.html"
    context = {"request": request, "user": getuser()}
    return templates.TemplateResponse(name=name, context=context)


@app.post("/submit")
async def submit(
    *,
    name: str = Form(...),
    description: str = Form(...),
    price: Decimal = Form(...),
) -> RedirectResponse:
    order = OrderIn(
        name=name,
        datetime=dt.datetime.now(),
        description=description,
        price=price,
    )
    add_order_to_db(order)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
