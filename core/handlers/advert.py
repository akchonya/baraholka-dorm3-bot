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
from ..utils.misc import redis
from core.db.models import Advert


# Create states
class StatesNewAdvert(StatesGroup):
    GET_CAPTION = State()
    GET_DESCRIPTION = State()
    GET_PRICE = State()

new_advert_router = Router()

MY_CHANNEL = "@testieman_group"

@new_advert_router.message(Command("new_advert"))
async def new_post_handler(message: Message, state: FSMContext):
    await redis.delete(
        "user_ads:" + str(message.from_user.id),
        "user_ads_pos:" + str(message.from_user.id)
        )
    await state.set_state(StatesNewAdvert.GET_CAPTION)
    await message.answer("назва?")

@new_advert_router.message(StatesNewAdvert.GET_CAPTION)
async def get_caption_handler(message: Message, state: FSMContext):
    await state.update_data(caption=message.text)
    await message.answer("ок. опис?")
    await state.set_state(StatesNewAdvert.GET_DESCRIPTION)

@new_advert_router.message(StatesNewAdvert.GET_DESCRIPTION)
async def get_description_handler(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("ок. ціна?")
    await state.set_state(StatesNewAdvert.GET_PRICE)

@new_advert_router.message(StatesNewAdvert.GET_PRICE)
async def get_price_handler(message: Message, state: FSMContext, session: AsyncSession):
    context_data = await state.get_data()
    caption = context_data.get("caption")
    description = context_data.get("description")
    price = float(message.text)

    await session.merge(Advert(
        caption=caption,
        description=description,
        price=price,
        room=311,
        user_id=int(message.from_user.id)
        )
    )
    await session.commit()

    await state.clear()

