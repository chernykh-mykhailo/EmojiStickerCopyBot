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

        me = await bot.me()
        bot_mention = f"@{me.username} "
        bot_mention_short = f"@{me.username}"

        text = event.text
        caption = event.caption

        updates = {}
        if text:
            if text.startswith(bot_mention) and text[len(bot_mention):].startswith("/"):
                updates["text"] = text[len(bot_mention):]
        
        if caption:
            if caption.startswith(bot_mention) and caption[len(bot_mention):].startswith("/"):
                updates["caption"] = caption[len(bot_mention):]

        if updates:
            event = event.model_copy(update=updates)

        return await handler(event, data)
