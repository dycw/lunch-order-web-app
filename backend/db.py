from __future__ import annotations

import datetime as dt
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import (
    DECIMAL,
    Column,
    Connection,
    Date,
    Engine,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    select,
)
from sqlalchemy.exc import NoResultFound

from backend.models import OrderIn, OrderOut

METADATA = MetaData()


Orders = Table(
    "orders",
    METADATA,
    Column("id", Integer, autoincrement=True, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("date", Date, nullable=False),
    Column("description", String(255)),
    Column("price", DECIMAL),
)
Users = Table(
    "users",
    METADATA,
    Column("id", Integer, primary_key=True),
    Column("name", String(255), unique=True),
)


DATABASE_URL = "sqlite:///./test.db"
ENGINE = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
METADATA.create_all(ENGINE)


# create


def add_order_to_db(
    order: OrderIn, /, *, engine_or_conn: Engine | Connection = ENGINE
) -> None:
    with _yield_conn(engine_or_conn=engine_or_conn) as conn:
        user_id = _get_user_id_from_db(order.name, engine_or_conn=conn)
        ins = Orders.insert().values(
            user_id=user_id,
            date=order.date,
            description=order.description,
            price=order.price,
        )
        _ = conn.execute(ins)


def _get_user_id_from_db(
    name: str, /, *, engine_or_conn: Engine | Connection = ENGINE
) -> int:
    sel = Users.select().where(Users.c.name == name)
    with _yield_conn(engine_or_conn=engine_or_conn) as conn:
        try:
            return conn.execute(sel).scalar_one()
        except NoResultFound:
            _add_user_to_db(name, engine_or_conn=engine_or_conn)
            return _get_user_id_from_db(name, engine_or_conn=engine_or_conn)


def _add_user_to_db(
    name: str, /, *, engine_or_conn: Engine | Connection = ENGINE
) -> None:
    ins = Users.insert().values(name=name)
    with _yield_conn(engine_or_conn=engine_or_conn) as conn:
        _ = conn.execute(ins)


# read


def get_orders_from_db(
    *, date: dt.date | None = None, engine_or_conn: Engine | Connection = ENGINE
) -> list[OrderOut]:
    sel = (
        select(
            Users.c.name, Orders.c.date, Orders.c.description, Orders.c.price
        )
        .select_from(Users)
        .join(Orders)
    )
    if date is not None:
        sel = sel.where(Orders.c.date == date)
    with _yield_conn(engine_or_conn=engine_or_conn) as conn:
        rows = conn.execute(sel).all()
    return [
        OrderOut(user=user, date=date, description=description, price=price)
        for user, date, description, price in rows
    ]


# utilities


@contextmanager
def _yield_conn(
    *, engine_or_conn: Engine | Connection = ENGINE
) -> Iterator[Connection]:
    if isinstance(engine_or_conn, Engine):
        with engine_or_conn.begin() as conn:
            yield conn
    else:
        yield engine_or_conn
