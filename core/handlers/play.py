from aiogram import Router, html
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models import User

play_router = Router()


@play_router.message(Command("play"))
async def cmd_play(message: Message, session: AsyncSession):
    """
    Handles /play command
    :param message: Telegram message with "/play" text
    :param session: DB connection session
    """
    await session.merge(User(user_id=message.from_user.id, username=message.from_user.username))
    await session.commit()

    await message.answer(f"Hi, {message.from_user.username}")

