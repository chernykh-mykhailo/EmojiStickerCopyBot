from aiogram import BaseMiddleware, Bot, types

class GuestMessageStripMiddleware(BaseMiddleware):
    """
    Middleware that strips the bot's username from the beginning of text/caption
    so that Command filters and other text-based filters can work properly
    in Guest Mode when the user mentions the bot like '@botname /start'.
    """
    async def __call__(self, handler, event: types.Message, data: dict):
        bot: Bot = data.get("bot")
        if not bot:
            return await handler(event, data)

        me = await bot.get_me()
        bot_mention = f"@{me.username.lower()}"

        text = event.text
        caption = event.caption

        updates = {}
        if text:
            clean_text = text.strip()
            if clean_text.lower().startswith(bot_mention):
                remainder = clean_text[len(bot_mention):].strip()
                if remainder.startswith("/"):
                    updates["text"] = remainder

        if caption:
            clean_caption = caption.strip()
            if clean_caption.lower().startswith(bot_mention):
                remainder = clean_caption[len(bot_mention):].strip()
                if remainder.startswith("/"):
                    updates["caption"] = remainder

        if updates:
            event = event.model_copy(update=updates)

        return await handler(event, data)
