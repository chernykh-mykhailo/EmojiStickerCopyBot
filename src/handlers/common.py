from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from services.user_service import UserService
from utils.l10n import l10n
from utils.guest import guest_safe_answer
from core.di import container

router = Router()


@router.message(Command("start"))
@router.guest_message(Command("start"))
async def cmd_start(message: types.Message):
    user_service = container.resolve(UserService)
    user = await user_service.get_or_create_user(
        tg_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        language_code=message.from_user.language_code or "uk",
    )

    welcome_text = l10n.get_text(user.language_code, "msg-start")
    await guest_safe_answer(message, welcome_text, parse_mode="HTML")


@router.message(Command("cancel", "reset"))
@router.guest_message(Command("cancel", "reset"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    await state.clear()
    locale = message.from_user.language_code or "uk"
    if current_state is None:
        await guest_safe_answer(
            message,
            l10n.get_text(locale, "msg-nothing-to-cancel"),
            reply_markup=types.ReplyKeyboardRemove(),
        )
    else:
        await guest_safe_answer(
            message,
            l10n.get_text(locale, "msg-cancelled"),
            reply_markup=types.ReplyKeyboardRemove(),
        )
