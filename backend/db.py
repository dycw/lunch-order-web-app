from __future__ import annotations

import datetime as dt
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import (
    Column,
    Connection,
    Engine,
    ForeignKey,
    MetaData,
    Table,
    create_engine,
    func,
    select,
)
from sqlalchemy.dialects.sqlite import DATETIME, DECIMAL, INTEGER, VARCHAR
from sqlalchemy.exc import NoResultFound

from backend.models import OrderIn, OrderOut

METADATA = MetaData()


Orders = Table(
    "orders",
    METADATA,
    Column("id", INTEGER, autoincrement=True, primary_key=True),
    Column("datetime", DATETIME, nullable=False, default=dt.datetime.now),
    Column("user_id", INTEGER, ForeignKey("users.id")),
    Column("description", VARCHAR(255), nullable=False),
    Column("price", DECIMAL, nullable=False),
)
Users = Table(
    "users",
    METADATA,
    Column("id", INTEGER, autoincrement=True, primary_key=True),
    Column("name", VARCHAR(255), nullable=False, unique=True),
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
            datetime=order.datetime,
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
    *,
    date: dt.date | None = None,
    datetime: dt.datetime | None = None,
    engine_or_conn: Engine | Connection = ENGINE,
) -> list[OrderOut]:
    sel = (
        select(
            Orders.c.datetime,
            Users.c.name,
            Orders.c.description,
            Orders.c.price,
        )
        .select_from(Orders)
        .join(Users)
    )
    if date is not None:
        sel = sel.where(func.DATE(Orders.c.datetime) == date)
    if datetime is not None:
        sel = sel.where(Orders.c.datetime == datetime)
    sel = sel.order_by(Orders.c.datetime.desc())
    with _yield_conn(engine_or_conn=engine_or_conn) as conn:
        rows = conn.execute(sel).all()
    return [
        OrderOut(
            datetime=datetime, user=user, description=description, price=price
        )
        for datetime, user, description, price in rows
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
