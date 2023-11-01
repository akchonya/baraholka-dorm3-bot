'''
/start greets a user
'''

from aiogram import Router, html, F
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile
from aiogram.types import ReplyKeyboardRemove


start_router = Router()


@start_router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(f"<b>привіт, {html.unparse(message.from_user.first_name)}!</b>",
                        reply_markup=ReplyKeyboardRemove())
        