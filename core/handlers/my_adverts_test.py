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


@my_router.message(Command("ads"))
async def ads_handler(message: Message, session: AsyncSession):
    # Get user's ads from db
    ads = await session.execute(select(Advert).where(Advert.user_id == int(message.from_user.id)))
    ads.scalars().all()

    # Set an user_id
    user_id = message.from_user.id

    # Set the initial index 
    user_pos[user_id] = 0

    # Message: {caption of an ad} + ikb
    await message.answer(f"{ads[user_pos[user_id]].caption}", reply_markup=keyboard)
    

@my_router.callback_query(F.data.startswith("ad_"))
async def callbacks_ad(callback: CallbackQuery):
    # Get an action and user_id
    action = callback.data.split("_")[1]
    user_id = callback.from_user.id

    # If the action is next and index is not the last: 
    if action == "next" and user_pos[user_id] != len(ads) - 1:
        # Ignore the error with the same message after the edit
        with suppress(TelegramBadRequest):
            # Increment the index
            user_pos[user_id] += 1

            # Message: another ad with the same kb
            await callback.message.edit_text(f"{ads[user_pos[user_id]]}", reply_markup=keyboard)
            await callback.answer()
    
    # If the action is prev and index isn't the first
    elif action == "prev" and user_pos[user_id] != 0:
        # Ignore the error with the same message after the edit
        with suppress(TelegramBadRequest):
            # Decrement the index
            user_pos[user_id] -= 1

            # Message: previous ad with the same kb 
            await callback.message.edit_text(f"{ads[user_pos[user_id]]}", reply_markup=keyboard)
            await callback.answer()
    
    else:
        await callback.answer()

    