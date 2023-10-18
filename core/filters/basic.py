from aiogram.types import Message
from aiogram.filters import Filter


class contains_vahta(Filter):
    async def __call__(self, message: Message) -> bool:
        return 