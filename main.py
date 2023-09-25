import logging
import sys
from os import getenv
from dotenv import load_dotenv
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from core.handlers.start import start_router
from core.handlers.new_post import new_post_router


load_dotenv()

BOT_TOKEN = getenv("BOT_TOKEN")

WEB_SERVER_HOST = getenv("WEB_SERVER_HOST")
# Port for incoming request from reverse proxy. 
WEB_SERVER_PORT = 8443

# Path to webhook route, on which Telegram will send requests
WEBHOOK_PATH = f"/bot/{BOT_TOKEN}"
# Secret key to validate requests from Telegram (optional)
WEBHOOK_SECRET = getenv("WEBHOOK_SECRET")
BASE_WEBHOOK_URL = getenv("BASE_WEBHOOK_URL")


async def on_startup(bot: Bot) -> None:
    # Set webhook 
    await bot.set_webhook(f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}", 
                          secret_token=WEBHOOK_SECRET,
                          allowed_updates=["message", "chat_member", ] # allow updates needed
                          )


def main() -> None:
    # Dispatcher is a root router
    dp = Dispatcher()

    # ... and all other routers should be attached to Dispatcher
    dp.include_routers(
        start_router,
        new_post_router)

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