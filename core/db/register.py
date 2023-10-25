from redis.asyncio.client import Redis
from sqlalchemy import select
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import sessionmaker
from ..utils.misc import redis
from .models import User
from sqlalchemy.ext.asyncio import AsyncSession


async def create_user(user_id: int, username: str, session: AsyncSession) -> None:
        await session.merge(User(user_id=user_id, username=username))
        await session.commit()


async def is_user_exists(user_id: int, session: AsyncSession) -> bool:
    res = await redis.get(name='is_user_exists:' + str(user_id))

    if not res:
        sql_res = await session.execute(select(User).where(User.user_id == user_id))
        sql_res = sql_res.scalars().all()
        await redis.set(name='is_user_exists:' + str(user_id), value=1 if len(sql_res) else 0)
        return bool(sql_res)
    else:
        return bool(res)