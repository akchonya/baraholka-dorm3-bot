#  Copyright (c) 2022.

from typing import Callable, Dict, Any, Awaitable, Union

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from core.db.register import is_user_exists, create_user


class RegisterCheck(BaseMiddleware):


    def __init__(self):
        pass

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any]
    ) -> Any:

        if event.web_app_data:
            return await handler(event, data)

        session = data["session"]
        user = event.from_user

        if not await is_user_exists(user_id=event.from_user.id, session=session):
            await create_user(user_id=event.from_user.id,
                              username=event.from_user.username, session=session, locale=user.language_code)
            await data['bot'].send_message(event.from_user.id, 'registered!')

        return await handler(event, data)