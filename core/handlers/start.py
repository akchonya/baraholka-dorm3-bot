'''
/start greets a user 
'''


from aiogram import types, Router
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardRemove


start_router = Router()

@start_router.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer(f"<b>привіт, {message.from_user.first_name}!</b>",
                         reply_markup=ReplyKeyboardRemove())

