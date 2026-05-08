import logging
from utils.image import ImageProcessor
from utils.video import VideoProcessor
from aiogram import Bot
from aiogram.types import BufferedInputFile, InputSticker

logger = logging.getLogger(__name__)


class StickerService:
    @staticmethod
    async def download_and_process(
        bot: Bot, file_id: str, target_format: str, source_sticker: any = None
    ) -> tuple[bytes | str, str]:
        """Download file and convert/resize it based on target pack type"""
        # Determine base format from target
        res_format = "static"
        if "anim" in target_format:
            res_format = "animated"
        elif "video" in target_format:
            res_format = "video"

        if target_format == "copy_only":
            return file_id, res_format

        # Fast path: if it's a sticker and matches target format perfectly
        if source_sticker and target_format != "emoji_nobg":
            source_type = "regular"
            if source_sticker.is_animated:
                source_type = "animated"
            elif source_sticker.is_video:
                source_type = "video"

            is_target_emoji = "emoji" in target_format
            is_source_emoji = source_sticker.type == "custom_emoji"

            if source_type in target_format and is_target_emoji == is_source_emoji:
                return file_id, source_type

        file = await bot.get_file(file_id)
        down_file = await bot.download_file(file.file_path)
        file_data = down_file.read()

        # Detect source type based on file path extension
        is_source_video = file.file_path.endswith(
            (".webm", ".mp4", ".gif", ".mov", ".mkv")
        )
        is_source_anim = file.file_path.endswith(".tgs")

        # 1. Handle Target: VIDEO
        if target_format in ["video", "custom_emoji_video"]:
            size = 100 if "emoji" in target_format else 512
            if is_source_video:
                return VideoProcessor.process_to_webm(file_data, size=size), "video"
            elif is_source_anim:
                return file_data, "animated"
            else:
                return (
                    VideoProcessor.process_to_webm(file_data, size=size, duration=2.9),
                    "video",
                )

        # 2. Handle Target: ANIMATED (TGS)
        if target_format in ["animated", "custom_emoji_anim"]:
            if is_source_anim:
                return file_data, "animated"
            else:
                # If we have a video but want animated emoji, we MUST use video format
                # unless we want a static frame.
                return file_data, "video" if is_source_video else "static"

        # 3. Handle Target: STATIC (Regular or Emoji)
        if target_format in ["regular", "copy", "custom_emoji", "emoji_nobg"]:
            if is_source_video or is_source_anim:
                file_data = VideoProcessor.extract_frame(file_data)
                return file_data, "static"

            if target_format in ["regular", "copy"]:
                return ImageProcessor.prepare_regular(file_data), "static"
            elif target_format == "custom_emoji":
                return ImageProcessor.prepare_emoji(file_data), "static"
            elif target_format == "emoji_nobg":
                return ImageProcessor.prepare_emoji_nobg(file_data), "static"

        return file_data, "static"

    @staticmethod
    def create_input_sticker(
        sticker_file: bytes | str, emoji: str, format: str
    ) -> InputSticker:
        """Create aiogram InputSticker object"""
        if isinstance(sticker_file, str):
            return InputSticker(sticker=sticker_file, emoji_list=[emoji], format=format)

        ext = (
            "png" if format == "static" else ("tgs" if format == "animated" else "webm")
        )
        return InputSticker(
            sticker=BufferedInputFile(sticker_file, filename=f"sticker.{ext}"),
            emoji_list=[emoji],
            format=format,
        )
