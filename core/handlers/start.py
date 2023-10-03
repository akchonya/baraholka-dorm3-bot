'''
/start greets a user and saves the user_id to the db
'''

from aiogram import Router, html
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.types import ReplyKeyboardRemove

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models import User

import simple_colors  


async def get_users_by_id(session: AsyncSession, user_id: int) -> list:

    user = await session.execute(
        select(User).where(User.user_id == user_id)
    )

    return user.scalars().all()



start_router = Router()


@start_router.message(CommandStart())
async def start_handler(message: Message, session: AsyncSession):
    """
    Handles /start command
    :param message: Telegram message with "/start" text
    :param session: DB connection session
    """
    user_in_db = await get_users_by_id(session, message.from_user.id)

    if user_in_db:
        await message.answer("Yes, you are already registered. ")
    else:
        await session.merge(User(user_id=message.from_user.id, username=message.from_user.username))
        await session.commit()

        await message.answer(f"<b>привіт, {message.from_user.first_name}!</b>",
                            reply_markup=ReplyKeyboardRemove())

