import io
import logging
from utils.image import ImageProcessor
from aiogram import Bot
from aiogram.types import BufferedInputFile, InputSticker

logger = logging.getLogger(__name__)

class StickerService:
    @staticmethod
    async def download_and_process(bot: Bot, file_id: str, set_type: str) -> bytes:
        """Download file and resize it based on target pack type"""
        file = await bot.get_file(file_id)
        down_file = await bot.download_file(file.file_path)
        file_data = down_file.read()

        if set_type == "copy_only" or set_type in ["animated", "video", "custom_emoji_anim", "custom_emoji_video"]:
            return file_data
        
        # Only use PIL for static formats
        if set_type in ["regular", "copy", "custom_emoji", "emoji_nobg"]:
            if set_type in ["regular", "copy"]:
                return ImageProcessor.prepare_regular(file_data)
            elif set_type == "custom_emoji":
                return ImageProcessor.prepare_emoji(file_data)
            elif set_type == "emoji_nobg":
                return ImageProcessor.prepare_emoji_nobg(file_data)
        
        return file_data

    @staticmethod
    def create_input_sticker(file_data: bytes, emoji: str, format: str) -> InputSticker:
        """Create aiogram InputSticker object"""
        ext = "png" if format == "static" else ("tgs" if format == "animated" else "webm")
        return InputSticker(
            sticker=BufferedInputFile(file_data, filename=f"sticker.{ext}"),
            emoji_list=[emoji],
            format=format
        )
