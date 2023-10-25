import logging
import sys

import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.fsm.storage.redis import RedisStorage

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from core.handlers.start import start_router
from core.handlers.new_post import new_post_router
from core.handlers.play import play_router
from core.handlers.advert import new_advert_router, my_router
# from core.handlers.my_adverts_test import my_router
from core.middlewares.db import DbSessionMiddleware
from core.db.engine import create_async_engine, procced_schemas, get_session_maker
from core.db.base import metadata
from core.utils.config import BOT_TOKEN, WEB_SERVER_HOST, WEBHOOK_SECRET, DB_URL, BASE_WEBHOOK_URL
from core.utils.commands import set_commands
from core.utils.misc import redis
from core.middlewares.register_check import RegisterCheck

# Port for incoming request from reverse proxy. 
WEB_SERVER_PORT = 8443

# Path to webhook route, on which Telegram will send requests
WEBHOOK_PATH = f"/bot/{BOT_TOKEN}"

async def on_startup(bot: Bot) -> None:
    await set_commands(bot)
    # Set webhook 
    await bot.set_webhook(f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}", 
                          secret_token=WEBHOOK_SECRET,
                          allowed_updates=["message", "chat_member", "callback_query"] # allow updates needed
                          )

    engine = create_async_engine(DB_URL)
    await procced_schemas(engine, metadata)


def main() -> None:

    # Dispatcher is a root router
    dp = Dispatcher(storage=RedisStorage(redis=redis))
    
    # Creating DB engine for PostgreSQL
    engine = create_async_engine(DB_URL)

    # Creating DB connections pool
    session_maker = get_session_maker(engine)

    dp.message.middleware(DbSessionMiddleware(session_maker))
    dp.message.middleware(RegisterCheck())

    # ... and all other routers should be attached to Dispatcher
    dp.include_routers(
        start_router,
        new_post_router,
        play_router,
        new_advert_router,
        my_router
        )

    # register other commands

    # Register startup hook to initialize webhook
    dp.startup.register(on_startup)
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(BOT_TOKEN, parse_mode=ParseMode.HTML)

    # Create aiohttp.web.Application instance
    app = web.Application()

    # Create an instance of request handler,
    # aiogram has few implementations for different cases of usage
    # In this example we use SimpleRequestHandler which is designed to handle simple cases
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET
    )
    # Register webhook handler on application
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    # Mount dispatcher startup and shutdown hooks to aiohttp application
    setup_application(app, dp, bot=bot)

    # And finally start webserver
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)

    
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())