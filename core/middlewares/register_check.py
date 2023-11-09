from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message

from core.db.register import is_user_exists, create_user


class RegisterCheck(BaseMiddleware):
    def __init__(self):
        pass

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        if event.web_app_data:
            return await handler(event, data)

        session = data["session"]
        user = event.from_user

        if not await is_user_exists(user_id=user.id, session=session):
            await create_user(user_id=user.id, username=user.username, session=session)
            await data["bot"].send_message(user.id, "registered!")

        return await handler(event, data)
