from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.types import ReplyKeyboardRemove


new_post_router = Router()

MY_CHANNEL = "@testieman_group"

@new_post_router.message(Command("new_post"))
async def new_post_handler(message: Message, bot: Bot):
    post = await bot.send_message(MY_CHANNEL, "горілка")
    await post.edit_text(post.text + "\n\nПРОДАНО!!")
