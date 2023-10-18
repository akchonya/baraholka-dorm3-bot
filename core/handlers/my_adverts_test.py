from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils.callback_answer import CallbackAnswer
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.methods import edit_message_text
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models import Advert

from contextlib import suppress
from aiogram.exceptions import TelegramBadRequest


my_router = Router()

buttons = [
    [
        InlineKeyboardButton(text="←", callback_data="ad_prev"),
        InlineKeyboardButton(text="→", callback_data="ad_next")
    ],
]
keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

user_pos = {}
ads = ("1st", "2nd", "3rd", "4th")


@my_router.message(Command("ads"))
async def ads_handler(message: Message):
    user_id = message.from_user.id
    user_pos[user_id] = 0
    await message.answer(f"{ads[user_pos[user_id]]}", reply_markup=keyboard)
    
@my_router.callback_query(F.data.startswith("ad_"))
async def callbacks_ad(callback: CallbackQuery):
    action = callback.data.split("_")[1]
    user_id = callback.from_user.id
    if action == "next" and user_pos[user_id] != len(ads) - 1:
        with suppress(TelegramBadRequest):
            user_pos[user_id] += 1
            await callback.message.edit_text(f"{ads[user_pos[user_id]]}", reply_markup=keyboard)
            await callback.answer()
    
    elif action == "prev" and user_pos[user_id] != 0:
        with suppress(TelegramBadRequest):
            user_pos[user_id] -= 1
            await callback.message.edit_text(f"{ads[user_pos[user_id]]}", reply_markup=keyboard)
            await callback.answer()
    
    else:
        await callback.answer()

    