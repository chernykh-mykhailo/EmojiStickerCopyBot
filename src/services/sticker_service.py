import logging
from utils.image import ImageProcessor
from utils.video import VideoProcessor
from aiogram import Bot
from aiogram.types import BufferedInputFile, InputSticker

logger = logging.getLogger(__name__)


class StickerService:
    @staticmethod
    async def download_and_process(bot: Bot, file_id: str, target_format: str) -> bytes:
        """Download file and convert/resize it based on target pack type"""
        file = await bot.get_file(file_id)
        down_file = await bot.download_file(file.file_path)
        file_data = down_file.read()

        # If it's a clone/copy without changes and formats match, skip processing
        if target_format == "copy_only":
            return file_data

        # Detect source type based on file path extension
        is_source_video = file.file_path.endswith(
            (".webm", ".mp4", ".gif", ".mov", ".mkv")
        )
        is_source_anim = file.file_path.endswith(".tgs")

        # 1. Handle Target: VIDEO
        if target_format in ["video", "custom_emoji_video"]:
            size = 100 if "emoji" in target_format else 512
            if is_source_video:
                return VideoProcessor.process_to_webm(file_data, size=size)
            elif is_source_anim:
                # Can't easily convert TGS to video in this setup, return as is and hope for the best
                # (usually TGS packs are not mixed with video)
                return file_data
            else:
                # Convert static image to a 3s static video (WEBM)
                # Actually, Telegram allows static video stickers (1 frame webm)
                return VideoProcessor.process_to_webm(file_data, size=size, duration=3)

        # 2. Handle Target: ANIMATED (TGS)
        if target_format in ["animated", "custom_emoji_anim"]:
            if is_source_anim:
                return file_data
            else:
                # We can't convert static/video to TGS (Lottie).
                # This should ideally be handled by UI (disallowing adding static to anim pack)
                # For now, return as is.
                return file_data

        # 3. Handle Target: STATIC (Regular or Emoji)
        if target_format in ["regular", "copy", "custom_emoji", "emoji_nobg"]:
            # If source is video/anim, extract first frame
            if is_source_video or is_source_anim:
                file_data = VideoProcessor.extract_frame(file_data)

            if target_format in ["regular", "copy"]:
                return ImageProcessor.prepare_regular(file_data)
            elif target_format == "custom_emoji":
                return ImageProcessor.prepare_emoji(file_data)
            elif target_format == "emoji_nobg":
                return ImageProcessor.prepare_emoji_nobg(file_data)

        return file_data

    @staticmethod
    def create_input_sticker(file_data: bytes, emoji: str, format: str) -> InputSticker:
        """Create aiogram InputSticker object"""
        ext = (
            "png" if format == "static" else ("tgs" if format == "animated" else "webm")
        )
        return InputSticker(
            sticker=BufferedInputFile(file_data, filename=f"sticker.{ext}"),
            emoji_list=[emoji],
            format=format,
        )
