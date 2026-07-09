from aiogram import types
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
import uuid

async def guest_safe_answer(message: types.Message, text: str, **kwargs):
    if getattr(message, "guest_query_id", None):
        return await message.answer_guest_query(
            result=InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="Reply",
                input_message_content=InputTextMessageContent(
                    message_text=text,
                    parse_mode=kwargs.get("parse_mode")
                ),
                reply_markup=kwargs.get("reply_markup")
            )
        )
    else:
        return await message.answer(text, **kwargs)

async def guest_safe_reply(message: types.Message, text: str, **kwargs):
    if getattr(message, "guest_query_id", None):
        return await message.answer_guest_query(
            result=InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="Reply",
                input_message_content=InputTextMessageContent(
                    message_text=text,
                    parse_mode=kwargs.get("parse_mode")
                ),
                reply_markup=kwargs.get("reply_markup")
            )
        )
    else:
        return await message.reply(text, **kwargs)

async def guest_safe_edit_text(callback: types.CallbackQuery, text: str, **kwargs):
    if callback.inline_message_id:
        return await callback.bot.edit_message_text(
            text=text,
            inline_message_id=callback.inline_message_id,
            **kwargs
        )
    else:
        return await callback.message.edit_text(text, **kwargs)
