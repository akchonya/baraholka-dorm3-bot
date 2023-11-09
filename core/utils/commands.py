from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat
from core.utils.config import ADMIN_ID


MODER = ADMIN_ID[1]
ADMIN = ADMIN_ID[0]

user_commands = [
    BotCommand(command="start", description="start"),
    BotCommand(command="new_advert", description="new advert"),
    BotCommand(command="ads", description="show your ads"),
]

moderator_commands = user_commands + [BotCommand(command="moder", description="moder")]


admin_commands = moderator_commands + [BotCommand(command="admin", description="admin")]


async def set_commands(bot: Bot):
    await bot.set_my_commands(user_commands, BotCommandScopeDefault())
    await bot.set_my_commands(
        moderator_commands, scope=BotCommandScopeChat(chat_id=MODER)
    )
    await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=ADMIN))
