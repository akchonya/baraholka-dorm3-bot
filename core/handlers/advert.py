"""
Adverts module
"""

from contextlib import suppress

import msgpack
from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from core.db.models import Advert
from core.keyboards import my_ads_ikb as keyboard
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..utils.misc import redis


async def edit_advert(advert: dict):
    """Function for creating ads messages

    Args:
        advert (dict): 'caption', 'description', 'price', 'user_id'

    Returns:
        msg (str): ad message
    """
    msg = (
        f"<b>{advert['caption']}</b>\n"
        f"{advert['description']}\n\n"
        f"ціна: {advert['price']}\n\n"
        f"звертатися до "
        f"<a href='tg://user?id={advert['user_id']}'>автора оголошення</a>"
    )

    return msg


# Create states
class StatesNewAdvert(StatesGroup):
    GET_CAPTION = State()
    GET_DESCRIPTION = State()
    GET_PRICE = State()
    GET_ROOM = State()
    GET_PHOTO = State()


new_advert_router = Router()


MY_CHANNEL = "@testieman_group"


# Ask for a caption
@new_advert_router.message(Command("new_advert"))
async def new_post_handler(message: Message, state: FSMContext):
    """New advert start handler

    Args:
        message (Message)
        state (FSMContext)
    """
    await redis.delete(
        "user_ads:" + str(message.from_user.id),
        "user_ads_pos:" + str(message.from_user.id),
    )
    await state.set_state(StatesNewAdvert.GET_CAPTION)
    await message.answer("назва?")


# A cancelation option
@new_advert_router.message(Command("cancel"), StateFilter(StatesNewAdvert))
@new_advert_router.message(F.text.casefold() == "cancel", StateFilter(StatesNewAdvert))
async def cancel_handler(message: Message, state: FSMContext) -> None:
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    print(current_state)
    if current_state is None:
        return

    await state.clear()
    await message.answer(
        "<b>відмінено створення нового оголошення</b>.\nповертайтеся ще :(",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML",
    )


# Save the caption and ask for a description
@new_advert_router.message(F.text, StatesNewAdvert.GET_CAPTION)
async def get_caption_handler(message: Message, state: FSMContext):
    await state.update_data(caption=message.text)
    await message.answer("ок. опис?")
    await state.set_state(StatesNewAdvert.GET_DESCRIPTION)


@new_advert_router.message(StatesNewAdvert.GET_CAPTION)
async def unwanted_caption_handler(message: Message):
    await message.answer(
        "<b>назва має бути текстом.</b> спробуйте ще раз"
        "\nнатисніть /cancel для відміни створення оголошення",
        parse_mode="HTML",
    )


# Save the description and ask for a price
@new_advert_router.message(F.text, StatesNewAdvert.GET_DESCRIPTION)
async def get_description_handler(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("ок. ціна?")
    await state.set_state(StatesNewAdvert.GET_PRICE)


@new_advert_router.message(StatesNewAdvert.GET_DESCRIPTION)
async def unwanted_description_handler(message: Message):
    await message.answer(
        "<b>опис має бути текстом.</b> спробуйте ще раз"
        "\nнатисніть /cancel для відміни створення оголошення",
        parse_mode="HTML",
    )


# Save the price and ask for a room
@new_advert_router.message(F.text, StatesNewAdvert.GET_PRICE)
async def get_price_handler(message: Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer("ок. кімната? якщо не хочете вказувати - натисніть /skip")
    await state.set_state(StatesNewAdvert.GET_ROOM)


@new_advert_router.message(StatesNewAdvert.GET_PRICE)
async def unwanted_price_handler(message: Message):
    await message.answer(
        "<b>ціна має бути текстом.</b> спробуйте ще раз"
        "\nнатисніть /cancel для відміни створення оголошення",
        parse_mode="HTML",
    )


# Skip the room and ask for a photo
@new_advert_router.message(F.text == "/skip", StatesNewAdvert.GET_ROOM)
async def skip_room_handler(message: Message, state: FSMContext):
    await state.update_data(room="не вказано.")
    await message.answer(
        "ок, забили на кімнату. будете додавати фото? натисніть /skip якщо ні"
    )
    await state.set_state(StatesNewAdvert.GET_PHOTO)


# Save the room and ask for a photo
@new_advert_router.message(F.text, StatesNewAdvert.GET_ROOM)
async def get_room_handler(message: Message, state: FSMContext):
    await state.update_data(room=message.text)
    await message.answer(
        "ок, записали кімнату. будете додавати фото? натисніть /skip якщо ні"
    )
    await state.set_state(StatesNewAdvert.GET_PHOTO)


@new_advert_router.message(StatesNewAdvert.GET_ROOM)
async def unwanted_room_handler(message: Message):
    await message.answer(
        "<b>кімната має бути текстом.</b> спробуйте ще раз"
        "\nнатисніть /cancel для відміни створення оголошення"
        "\nнатисніть /skip щоб пропустити додавання кімнати",
        parse_mode="HTML",
    )


# Skip the photo and save everything
@new_advert_router.message(F.text == "/skip", StatesNewAdvert.GET_PHOTO)
async def skip_photo_handler(
    message: Message, state: FSMContext, session: AsyncSession
):
    context_data = await state.get_data()
    caption = context_data.get("caption")
    description = context_data.get("description")
    price = context_data.get("price")
    room = context_data.get("room")

    await session.merge(
        Advert(
            caption=caption,
            description=description,
            price=price,
            room=room,
            user_id=int(message.from_user.id),
        )
    )

    await session.commit()
    await state.clear()
    await message.answer("все збережено. можете переглянути в /ads")


# Save the photo and save everything
@new_advert_router.message(F.photo, StatesNewAdvert.GET_PHOTO)
async def get_photo_handler(message: Message, state: FSMContext, session: AsyncSession):
    context_data = await state.get_data()
    caption = context_data.get("caption")
    description = context_data.get("description")
    price = context_data.get("price")
    room = context_data.get("room")

    await session.merge(
        Advert(
            caption=caption,
            description=description,
            price=price,
            room=room,
            user_id=int(message.from_user.id),
        )
    )

    await session.commit()
    await state.clear()
    await message.answer("все збережено. можете переглянути в /ads")


@new_advert_router.message(StatesNewAdvert.GET_PHOTO)
async def unwanted_photo_handler(message: Message):
    await message.answer(
        "<b>помилка.</b> спробуйте ще раз"
        "\nнатисніть /cancel для відміни створення оголошення"
        "\nнатисніть /skip щоб пропустити додавання фото",
        parse_mode="HTML",
    )


my_router = Router()


@my_router.message(Command("ads"))
async def ads_handler(message: Message, session: AsyncSession):
    # Set an user_id
    user_id = message.from_user.id

    # Look for cache
    res = await redis.get(name="user_ads:" + str(user_id))

    # If None -> cache and use it
    if not res:
        sql_res = await session.execute(
            select(Advert).where(Advert.user_id == int(user_id))
        )
        sql_res = sql_res.scalars().all()

        # If there aren't any ads -> send a message and stop operation
        if len(sql_res) == 0:
            await message.answer(
                "поки пусто :(\nви можете створити оголошення за допомогою /new_advert"
            )
            return "abort"

        # Turn rows into dicts
        ads = []
        for r in sql_res:
            # Don't accept _sa_instance_state key
            r = {k: v for (k, v) in r.__dict__.items() if k != "_sa_instance_state"}
            ads.append(r)

        # Pack the list of dictionaries and cache to the redis db
        await redis.set(
            name="user_ads:" + str(user_id),
            value=msgpack.packb(ads, use_bin_type=True),
            ex=3600,
        )

    # If there already was cache -> use it
    else:
        val = await redis.get("user_ads:" + str(user_id))
        # Unpack values
        ads = msgpack.unpackb(val, encoding="utf-8")

    # Set the initial index and add to the redis db
    user_pos = 0
    await redis.set(name="user_ads_pos:" + str(user_id), value=0, ex=3600)

    # Message: ad + ikb
    msg = await edit_advert(ads[user_pos])
    await message.answer(msg, reply_markup=keyboard, parse_mode="HTML")


@my_router.callback_query(F.data.startswith("ad_"))
async def callbacks_ad(callback: CallbackQuery):
    # Get an action and user_id
    action = callback.data.split("_")[1]
    user_id = callback.from_user.id

    # Get user position from the redis and turn it to int
    user_pos = await redis.get(name="user_ads_pos:" + str(user_id))
    user_pos = int(user_pos)

    # Get ads from the redis and unpack them
    val = await redis.get(name="user_ads:" + str(user_id))
    ads = msgpack.unpackb(val, encoding="utf-8")

    # If the action is next and index is not the last:
    if action == "next" and user_pos != len(ads) - 1:
        # Ignore the error with the same message after the edit
        with suppress(TelegramBadRequest):
            # Increment the index
            user_pos += 1
            await redis.set(
                name="user_ads_pos:" + str(user_id), value=user_pos, ex=3600
            )

            # Message: another ad with the same kb
            msg = await edit_advert(ads[user_pos])
            await callback.message.edit_text(
                msg, reply_markup=keyboard, parse_mode="HTML"
            )
            await callback.answer()

    # If the action is prev and index isn't the first
    elif action == "prev" and user_pos != 0:
        # Ignore the error with the same message after the edit
        with suppress(TelegramBadRequest):
            # Decrement the index
            user_pos -= 1
            await redis.set(
                name="user_ads_pos:" + str(user_id), value=user_pos, ex=3600
            )

            # Message: previous ad with the same kb
            msg = await edit_advert(ads[user_pos])
            await callback.message.edit_text(
                msg, reply_markup=keyboard, parse_mode="HTML"
            )
            await callback.answer()

    else:
        await callback.answer()
