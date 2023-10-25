from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)


my_ads_ikb = InlineKeyboardMarkup(keyboard=[
    [
        InlineKeyboardButton(text="←", callback_data="ad_prev"),
        InlineKeyboardButton(text="→", callback_data="ad_next")
    ]
])

