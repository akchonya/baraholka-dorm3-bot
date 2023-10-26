import datetime
from typing import List

from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from sqlalchemy import Column, BigInteger, VARCHAR, DATE, Integer

from core.db.base import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, primary_key=True)
    username = Column(VARCHAR(32), unique=False, nullable=True)
    reg_date = Column(DATE, default=datetime.date.today(), nullable=False)
    adverts: Mapped[List["Advert"]] = relationship()


    def __str__(self) -> str:
        return f"<User id: {self.user_id} | username: {self.username}>"


class Advert(Base):
    __tablename__ = "adverts"

    ad_id: Mapped[int] = mapped_column(Integer, autoincrement="auto", unique=True, nullable=False, primary_key=True)
    caption = Column(VARCHAR, unique=False, nullable=False)
    description = Column(VARCHAR, unique=False, nullable=False)
    price = Column(VARCHAR, unique=False, nullable=False)
    room = Column(Integer, unique=False, nullable=False)
    status = Column(VARCHAR, unique=False, default="active")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))

    def __str__(self) -> str:
        return f"\n<Advert: \n" \
        f"id: {self.ad_id}\n" \
        f"caption: {self.caption}>\n"