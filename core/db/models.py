from sqlalchemy import Column, BigInteger, VARCHAR

from core.db.base import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(BigInteger, unique=True, nullable=False, primary_key=True)
    username = Column(VARCHAR(32), unique=False, nullable=True)