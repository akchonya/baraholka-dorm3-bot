import msgpack

from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.types import CallbackQuery
from aiogram.utils.callback_answer import CallbackAnswer
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.methods import edit_message_text
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models import Advert
from core.utils.misc import redis

from contextlib import suppress
from aiogram.exceptions import TelegramBadRequest

from core.keyboards import my_ads_ikb as keyboard


my_router = Router()


@my_router.message(Command("ads"))
async def ads_handler(message: Message, session: AsyncSession):
    # Set an user_id
    user_id = message.from_user.id

    # Look for cache
    res = await redis.get(name="user_ads:" + str(user_id))

    # If None -> cache and use it 
    if not res:
        sql_res = await session.execute(select(Advert).where(Advert.user_id == int(user_id)))
        sql_res = sql_res.scalars().all()

        # Turn rows into dicts 
        ads = []
        for r in sql_res:
            # Don't accept _sa_instance_state key
            r = {k: v for (k, v) in r.__dict__.items()
                     if k != '_sa_instance_state'}
            ads.append(r)

        # Pack the list of dictionaries and cache to the redis db
        await redis.set(name="user_ads:" + str(user_id), value=msgpack.packb(ads, use_bin_type=True))
    
    # If there already was cache -> use it 
    else:
        val = await redis.get("user_ads:" + str(user_id))
        # Unpack values
        ads = msgpack.unpackb(val, encoding='utf-8')

    # Set the initial index and add to the redis db
    user_pos = 0
    await redis.set(name="user_ads_pos:" + str(user_id), value=0, ex=3600)

    # Message: caption of an ad + ikb
    await message.answer(f"{ads[user_pos]['caption']}", reply_markup=keyboard)


@my_router.callback_query(F.data.startswith("ad_"))
async def callbacks_ad(callback: CallbackQuery):
    # Get an action and user_id
    action = callback.data.split("_")[1]
    user_id = callback.from_user.id

    # Get user position from the redis and turn it to int 
    user_pos = await redis.get(name='user_ads_pos:' + str(user_id))
    user_pos = int(user_pos)

    # Get ads from the redis and unpack them
    val = await redis.get(name="user_ads:" + str(user_id))
    ads = msgpack.unpackb(val, encoding='utf-8')

    # If the action is next and index is not the last: 
    if action == "next" and user_pos != len(ads) - 1:

        # Ignore the error with the same message after the edit
        with suppress(TelegramBadRequest):

            # Increment the index
            user_pos += 1
            await redis.set(name="user_ads_pos:" + str(user_id), value=user_pos, ex=3600)

            # Message: another ad with the same kb
            await callback.message.edit_text(f"{ads[user_pos]['caption']}", reply_markup=keyboard)
            await callback.answer()
    
    # If the action is prev and index isn't the first
    elif action == "prev" and user_pos != 0:

        # Ignore the error with the same message after the edit
        with suppress(TelegramBadRequest):
            
            # Decrement the index
            user_pos -= 1
            await redis.set(name="user_ads_pos:" + str(user_id), value=user_pos, ex=3600)

            # Message: previous ad with the same kb 
            await callback.message.edit_text(f"{ads[user_pos]['caption']}", reply_markup=keyboard)
            await callback.answer()
    
    else:
        await callback.answer()

    