import logging
import asyncio
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
        """Wrapper for bot.add_sticker_to_set with retry logic and DB update"""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                await self.bot.add_sticker_to_set(
                    user_id=user_id, name=name, sticker=sticker
                )
                await self.sticker_repo.increment_count(name)
                return
            except Exception as e:
                error_msg = str(e)
                if "STICKERSET_INVALID" in error_msg and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    logger.warning(
                        f"Attempt {attempt + 1}: STICKERSET_INVALID for {name}. Retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                    continue

                logger.error(
                    f"Failed to add sticker to {name} after {attempt + 1} attempts: {e}"
                )
                raise

    async def get_sticker_set(self, name: str):
        return await self.bot.get_sticker_set(name)

    async def delete_pack(self, name: str):
        await self.sticker_repo.delete(name)
