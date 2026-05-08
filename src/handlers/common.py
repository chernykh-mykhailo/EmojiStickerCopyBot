from aiogram import Router, types
from aiogram.filters import Command
from services.user_service import UserService
from utils.l10n import l10n
from core.di import container

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_service = container.resolve(UserService)
    user = await user_service.get_or_create_user(
        tg_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        language_code=message.from_user.language_code or "uk",
    )

    welcome_text = l10n.get_text(user.language_code, "start-welcome")
    await message.answer(welcome_text)
