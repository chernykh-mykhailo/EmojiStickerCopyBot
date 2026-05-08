from aiogram import Bot
from aiogram.types import BotCommand


async def set_commands(bot: Bot):
    # Default (English)
    commands_en = [
        BotCommand(command="start", description="Main menu / Welcome"),
        BotCommand(command="packs", description="Manage sticker packs"),
    ]

    # Ukrainian
    commands_uk = [
        BotCommand(command="start", description="Головне меню"),
        BotCommand(command="packs", description="Керування паками"),
    ]

    # Set default commands
    await bot.set_my_commands(commands_en)

    # Set localized commands
    await bot.set_my_commands(commands_en, language_code="en")
    await bot.set_my_commands(commands_uk, language_code="uk")
