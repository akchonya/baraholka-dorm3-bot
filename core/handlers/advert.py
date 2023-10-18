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

user_data = {}

def get_keyboard(msg_id):
    buttons = [
        [
            InlineKeyboardButton(text="←", callback_data="ad_prev_{msg_id}"),
            InlineKeyboardButton(text="→", callback_data="ad_next_{msg_id}")
        ],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


# Create states
class StatesNewAdvert(StatesGroup):
    GET_CAPTION = State()
    GET_DESCRIPTION = State()
    GET_PRICE = State()

new_advert_router = Router()

MY_CHANNEL = "@testieman_group"

@new_advert_router.message(Command("new_advert"))
async def new_post_handler(message: Message, state: FSMContext):
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


my_adverts_router = Router()
@my_adverts_router.message(Command("my_adverts"))
async def my_adverts_handler(message: Message, session: AsyncSession):
    user_data[message.from_user.id] = 0
    adverts = await session.execute(
        select(Advert).where(Advert.user_id == int(message.from_user.id))
    )

    adverts = adverts.scalars().all()
    msg = await message.answer(adverts[0].caption)
    msg = msg.message_id 
    await message.answer("можна листати вправо вліво", reply_markup=get_keyboard(msg))

# @my_adverts_router.callback_query(F.data.startswith("ad_"))
# async def callbacks_num(bot: Bot, callback: CallbackQuery):
#     user_value = user_data.get(callback.from_user.id, 0)
#     data = callback.data.split("_")
#     print(f"\n\n{data}\n\n")
#     action = data[1]
#     msg = data[2]

#     if action == "next":
#         user_data[callback.from_user.id] = user_value+1
#         await bot.edit_message_text(chat_id=callback.from_user.id, message_id=msg, text="done")
#     elif action == "prev":
#         user_data[callback.from_user.id] = user_value-1
#         print("\nok\n")
        


    # await callback.answer()