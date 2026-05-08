import logging
from aiogram import Bot
from aiogram.types import InputSticker
from database.repositories.sticker_repo import StickerRepository

logger = logging.getLogger(__name__)


class PackService:
    def __init__(self, bot: Bot, sticker_repo: StickerRepository):
        self.bot = bot
        self.sticker_repo = sticker_repo

    async def create_new_set(
        self,
        user_id: int,
        name: str,
        title: str,
        stickers: list[InputSticker],
        sticker_type: str,
    ):
        """Wrapper for bot.create_new_sticker_set and DB registration"""
        await self.bot.create_new_sticker_set(
            user_id=user_id,
            name=name,
            title=title,
            stickers=stickers,
            sticker_type="regular"
            if sticker_type != "custom_emoji"
            else "custom_emoji",
        )
        await self.sticker_repo.create(
            name=name,
            title=title,
            creator_id=user_id,
            set_type=sticker_type,
            sticker_count=len(stickers),
        )

    async def add_sticker(self, user_id: int, name: str, sticker: InputSticker):
        """Wrapper for bot.add_sticker_to_set and DB update"""
        await self.bot.add_sticker_to_set(user_id=user_id, name=name, sticker=sticker)
        await self.sticker_repo.increment_count(name)

    async def get_sticker_set(self, name: str):
        return await self.bot.get_sticker_set(name)
