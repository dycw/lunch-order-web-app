from __future__ import annotations

import datetime as dt
from contextlib import contextmanager
from typing import Iterator
from uuid import UUID, uuid4

from sqlalchemy import (
    DECIMAL,
    Column,
    Connection,
    DateTime,
    Engine,
    ForeignKey,
    MetaData,
    String,
    Table,
    create_engine,
    func,
    select,
)
from sqlalchemy.exc import NoResultFound

from backend.models import OrderIn, OrderOut

METADATA = MetaData()


Orders = Table(
    "orders",
    METADATA,
    Column("id", String(36), primary_key=True),
    Column("datetime", DateTime, nullable=False, default=dt.datetime.now),
    Column("user_id", String(36), ForeignKey("users.id")),
    Column("description", String(255), nullable=False),
    Column("price", DECIMAL, nullable=False),
)
Users = Table(
    "users",
    METADATA,
    Column("id", String(36), primary_key=True),
    Column("name", String(255), nullable=False, unique=True),
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
            id=str(uuid4()),
            datetime=order.datetime,
            user_id=user_id,
            description=order.description,
            price=order.price,
        )
        _ = conn.execute(ins)


def _get_user_id_from_db(
    name: str, /, *, engine_or_conn: Engine | Connection = ENGINE
) -> UUID:
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
    ins = Users.insert().values(id=str(uuid4()), name=name)
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
            Orders.c.id,
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
            id=id_,
            datetime=datetime,
            user=user,
            description=description,
            price=price,
        )
        for id_, datetime, user, description, price in rows
    ]


# delete


def delete_order_from_db(
    id_: UUID, /, *, engine_or_conn: Engine | Connection = ENGINE
) -> None:
    del_ = Orders.delete().where(Orders.c.id == str(id_))
    with _yield_conn(engine_or_conn=engine_or_conn) as conn:
        _ = conn.execute(del_)


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
