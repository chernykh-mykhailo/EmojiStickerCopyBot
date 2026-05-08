import re
import asyncio
import logging
from aiogram import Router, F, Bot, types, html
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from core.di import container
from services.pack_service import PackService
from services.sticker_service import StickerService
from services.user_service import UserService
from database.repositories.sticker_repo import StickerRepository
from utils.l10n import l10n
from utils.image import ImageProcessor
from keyboards.inline import (
    get_packs_keyboard,
    get_cancel_keyboard,
    get_done_keyboard,
    get_copy_menu,
    get_user_packs_keyboard,
    get_disable_keyboard,
    get_format_selection,
    get_first_pack_keyboard,
    get_open_pack_keyboard,
    get_pack_manage_keyboard,
)

router = Router()
logger = logging.getLogger(__name__)


class PackCreation(StatesGroup):
    waiting_type = State()
    waiting_name = State()
    waiting_title = State()
    adding_items = State()
    cloning_source = State()
    cloning_title = State()
    cloning_name = State()


class CopyMode(StatesGroup):
    selecting_target = State()
    active = State()


@router.message(Command("packs"))
async def cmd_packs(message: types.Message):
    user_service = container.resolve(UserService)
    user = await user_service.get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name,
        message.from_user.language_code or "uk",
    )
    await message.answer(
        l10n.get_text(user.language_code, "packs-menu"),
        reply_markup=get_packs_keyboard(user.language_code),
    )


@router.callback_query(F.data.startswith("sticker_type:"))
async def select_type(callback: types.CallbackQuery, state: FSMContext):
    sticker_type = callback.data.split(":")[1]
    await state.update_data(sticker_type=sticker_type)

    user_service = container.resolve(UserService)
    user = await user_service.get_or_create_user(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.full_name,
        callback.from_user.language_code or "uk",
    )

    if sticker_type == "clone":
        await state.set_state(PackCreation.cloning_source)
        await callback.message.edit_text(
            l10n.get_text(user.language_code, "prompt-copy"),
            reply_markup=get_cancel_keyboard(user.language_code),
        )
    else:
        await state.set_state(PackCreation.waiting_title)
        await callback.message.edit_text(
            l10n.get_text(user.language_code, "prompt-title"),
            reply_markup=get_cancel_keyboard(user.language_code),
        )
    await callback.answer()


@router.message(PackCreation.waiting_title, F.text)
async def process_title(message: types.Message, state: FSMContext, bot: Bot):
    if not message.text:
        return
    title = message.text.strip()
    await state.update_data(pack_title=title)

    # Check if title can be used as short name (latin + digits)
    # Remove spaces and check if the result is valid
    slug = title.replace(" ", "")
    if re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", slug):
        # Title is good for link!
        await finalize_pack_setup(message, state, bot, slug, title)
    else:
        # Title is not good for link, ask for one
        await state.set_state(PackCreation.waiting_name)
        await message.reply(
            l10n.get_text(message.from_user.language_code, "prompt-name")
        )


@router.message(PackCreation.waiting_name, F.text)
async def process_name(message: types.Message, state: FSMContext, bot: Bot):
    if not message.text:
        return
    name = message.text.strip()
    if not re.match(r"^[a-zA-Z0-9_]+$", name):
        await message.reply(
            l10n.get_text(message.from_user.language_code, "err-invalid-name")
        )
        return

    data = await state.get_data()
    await finalize_pack_setup(message, state, bot, name, data.get("pack_title"))


async def finalize_pack_setup(
    message: types.Message, state: FSMContext, bot: Bot, name_short: str, title: str
):
    data = await state.get_data()
    sticker_type = data.get("sticker_type")

    me = await bot.get_me()
    full_name_base = f"{name_short}_by_{me.username}"
    full_title = f"{title} by @{me.username}"

    await state.update_data(
        pack_name_short=name_short, full_name=full_name_base, full_title=full_title
    )

    # Create pack with placeholder immediately
    pack_service = container.resolve(PackService)
    sticker_service = container.resolve(StickerService)

    try:
        # Use 100x100 for emoji, 512x512 for regular
        size = 100 if sticker_type == "custom_emoji" else 512
        placeholder_data = ImageProcessor.get_placeholder(size)

        # Determine format
        sticker_format = "static"  # Placeholder is always static

        input_sticker = sticker_service.create_input_sticker(
            placeholder_data, "⏳", sticker_format
        )

        await pack_service.create_new_set(
            user_id=message.from_user.id,
            name=full_name_base,
            title=full_title,
            stickers=[input_sticker],
            sticker_type=sticker_type,
        )

        await state.update_data(pack_created=True, placeholder_active=True)
        await state.set_state(PackCreation.adding_items)

        await message.reply(
            l10n.get_text(message.from_user.language_code, "prompt-media", title=title),
            reply_markup=get_done_keyboard(message.from_user.language_code),
        )
    except Exception as e:
        logger.exception(f"Error creating pack with placeholder: {e}")
        await message.reply(
            l10n.get_text(
                message.from_user.language_code, "err-generic", error=html.quote(str(e))
            )
        )


@router.message(
    PackCreation.adding_items, F.sticker | F.photo | F.video | F.animation | F.document
)
async def process_item(message: types.Message, state: FSMContext, bot: Bot):
    sticker_service = container.resolve(StickerService)
    pack_service = container.resolve(PackService)
    data = await state.get_data()

    sticker_type = data.get("sticker_type")
    pack_name_short = data.get("pack_name_short")

    me = await bot.get_me()
    full_name = data.get("full_name")
    if not full_name:
        full_name = f"{pack_name_short}_by_{me.username}"

    # Extract file_id from any supported media
    if message.sticker:
        file_id = message.sticker.file_id
        emoji = message.sticker.emoji or "😀"
    elif message.photo:
        file_id = message.photo[-1].file_id
        emoji = "🖼"
    elif message.video:
        file_id = message.video.file_id
        emoji = "🎥"
    elif message.animation:
        file_id = message.animation.file_id
        emoji = "✨"
    elif message.document:
        # Check if it's an image or video file
        mime = message.document.mime_type or ""
        if not (mime.startswith("image/") or mime.startswith("video/")):
            await message.reply(
                "❌ This file type is not supported. Please send an image or video."
            )
            return
        file_id = message.document.file_id
        emoji = "📄"
    else:
        return

    proc_msg = await message.answer(
        l10n.get_text(message.from_user.language_code, "processing-item")
    )

    try:
        # target_format should match pack type
        target_format = "regular"
        if sticker_type == "custom_emoji":
            target_format = "custom_emoji"
        elif sticker_type == "animated":
            target_format = "animated"
        elif sticker_type == "video":
            target_format = "video"

        file_data = await sticker_service.download_and_process(
            bot, file_id, target_format
        )

        # Determine format for InputSticker
        sticker_format = "static"
        if sticker_type == "animated":
            sticker_format = "animated"
        elif sticker_type == "video":
            sticker_format = "video"

        input_sticker = sticker_service.create_input_sticker(
            file_data, emoji, sticker_format
        )

        await pack_service.add_sticker(message.from_user.id, full_name, input_sticker)

        # If placeholder is active, delete it
        if data.get("placeholder_active"):
            try:
                # We need to get the set to find the placeholder (first sticker)
                sticker_set = await bot.get_sticker_set(full_name)
                if sticker_set.stickers:
                    await bot.delete_sticker_from_set(sticker_set.stickers[0].file_id)
                await state.update_data(placeholder_active=False)
            except Exception as e:
                logger.warning(f"Failed to delete placeholder: {e}")

        await proc_msg.delete()
        await message.answer(
            l10n.get_text(message.from_user.language_code, "item-added", count="?")
        )
    except Exception as e:
        logger.exception(f"Error processing item: {e}")
        await proc_msg.edit_text(
            l10n.get_text(
                message.from_user.language_code, "err-generic", error=html.quote(str(e))
            )
        )


@router.message(PackCreation.cloning_source, F.sticker | F.text)
async def process_cloning_source(message: types.Message, state: FSMContext, bot: Bot):
    sticker_set_name = None
    if message.sticker:
        sticker_set_name = message.sticker.set_name
    elif message.text:
        text = message.text.strip()
        if "addstickers/" in text:
            sticker_set_name = text.split("addstickers/")[1].split()[0]
        elif "/" not in text:
            sticker_set_name = text

    if not sticker_set_name:
        await message.reply("❌ Please send a sticker or a valid pack name.")
        return

    try:
        source_set = await bot.get_sticker_set(sticker_set_name)
        await state.update_data(
            source_set_name=sticker_set_name, source_title=source_set.title
        )
        await state.set_state(PackCreation.cloning_title)
        await message.reply(
            l10n.get_text(message.from_user.language_code, "prompt-title")
        )
    except Exception as e:
        await message.reply(
            l10n.get_text(message.from_user.language_code, "err-generic", error=str(e))
        )


@router.message(PackCreation.cloning_title, F.text)
async def process_cloning_title(message: types.Message, state: FSMContext, bot: Bot):
    if not message.text:
        return
    title = message.text.strip()
    await state.update_data(cloning_title=title)

    # Check if title can be used as short name (latin + digits)
    slug = title.replace(" ", "")
    if re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", slug):
        # Title is good for link!
        await finalize_cloning_setup(message, state, bot, slug, title)
    else:
        # Title is not good for link, ask for one
        await state.set_state(PackCreation.cloning_name)
        await message.reply(
            l10n.get_text(message.from_user.language_code, "prompt-name")
        )


async def finalize_cloning_setup(
    message: types.Message, state: FSMContext, bot: Bot, name_short: str, title: str
):
    data = await state.get_data()
    source_set_name = data.get("source_set_name")

    me = await bot.get_me()
    full_name = f"{name_short}_by_{me.username}"
    full_title = f"{title} by @{me.username}"

    target_format = data.get("target_format", "regular")

    await message.reply(
        l10n.get_text(message.from_user.language_code, "copy-started", title=title)
    )

    asyncio.create_task(
        run_cloning(
            message.from_user.id,
            bot,
            source_set_name,
            full_name,
            full_title,
            message.from_user.language_code,
            target_format,
        )
    )
    await state.clear()


@router.message(PackCreation.cloning_name, F.text)
async def process_cloning_name(message: types.Message, state: FSMContext, bot: Bot):
    if not message.text:
        return
    name_short = message.text.strip()
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", name_short):
        await message.reply(
            l10n.get_text(message.from_user.language_code, "err-invalid-name")
        )
        return

    data = await state.get_data()
    title = data.get("cloning_title")
    await finalize_cloning_setup(message, state, bot, name_short, title)


async def run_cloning(
    user_id: int,
    bot: Bot,
    source_name: str,
    target_name: str,
    target_title: str,
    locale: str,
    target_format: str = "regular",
):
    pack_service = container.resolve(PackService)
    sticker_service = container.resolve(StickerService)

    try:
        source_set = await bot.get_sticker_set(source_name)

        # Determine target set type
        set_type = "regular"
        if "emoji" in target_format:
            set_type = "custom_emoji"
        elif target_format == "animated":
            set_type = "animated"
        elif target_format == "video":
            set_type = "video"

        # Determine if we need to process or just copy
        # If formats match and it's not emoji conversion, we can skip PIL
        source_type = "regular"
        if source_set.is_animated:
            source_type = "animated"
        elif source_set.is_video:
            source_type = "video"

        # Force processing for the first sticker to ensure exact dimensions for set creation
        first = source_set.stickers[0]
        file_data = await sticker_service.download_and_process(
            bot, first.file_id, target_format
        )

        # Determine format
        if "anim" in target_format or source_type == "animated":
            sticker_format = "animated"
        elif "video" in target_format or source_type == "video":
            sticker_format = "video"
        else:
            sticker_format = "static"

        input_sticker = sticker_service.create_input_sticker(
            file_data, first.emoji or "😀", sticker_format
        )
        await pack_service.create_new_set(
            user_id, target_name, target_title, [input_sticker], set_type
        )

        for s in source_set.stickers[1:]:
            # For remaining stickers, we can use copy_only if formats match
            needs_processing_rest = (set_type != source_type) or (
                target_format == "emoji_nobg"
            )
            file_data = await sticker_service.download_and_process(
                bot, s.file_id, target_format if needs_processing_rest else "copy_only"
            )

            input_sticker = sticker_service.create_input_sticker(
                file_data, s.emoji or "😀", sticker_format
            )
            await pack_service.add_sticker(user_id, target_name, input_sticker)
            await asyncio.sleep(0.4)

        await bot.send_message(
            user_id,
            l10n.get_text(
                locale, "create-success", title=target_title, name=target_name
            ),
            reply_markup=get_open_pack_keyboard(locale, target_name),
        )
    except Exception as e:
        logger.exception(f"Error during cloning: {e}")
        await bot.send_message(
            user_id, f"❌ Error during cloning: {html.quote(str(e))}"
        )


# --- New Interactive Copy Logic ---


@router.message(
    F.sticker
    | F.photo
    | F.video
    | F.animation
    | F.document
    | (F.text & ~F.text.startswith("/"))
)
async def handle_incoming_media(message: types.Message, state: FSMContext, bot: Bot):
    # If in active copy mode, add immediately
    current_state = await state.get_state()
    data = await state.get_data()

    if current_state == CopyMode.active.state:
        target_pack = data.get("target_pack")
        if target_pack:
            await add_item_to_pack(message, target_pack, state, bot)
            return

    # Check if it's an emoji or media
    is_emoji = False
    if message.text and len(message.text) <= 2:  # Simple emoji check
        is_emoji = True

    if not any(
        [
            message.sticker,
            message.photo,
            message.video,
            message.animation,
            message.document,
            is_emoji,
        ]
    ):
        return

    # Ask what to do
    sticker_type = "static"
    file_id = None
    emoji = "🖼"
    set_name = None

    if message.sticker:
        file_id = message.sticker.file_id
        emoji = message.sticker.emoji or "😀"
        set_name = message.sticker.set_name
        if message.sticker.is_animated:
            sticker_type = "animated"
        elif message.sticker.is_video:
            sticker_type = "video"
    elif message.photo:
        file_id = message.photo[-1].file_id
    elif message.video:
        file_id = message.video.file_id
        sticker_type = "video"
        emoji = "🎥"
    elif message.animation:
        file_id = message.animation.file_id
        sticker_type = "video"  # Animations (GIFs) are converted to video stickers
        emoji = "✨"
    elif message.document:
        mime = message.document.mime_type or ""
        if mime.startswith("video/"):
            sticker_type = "video"
        file_id = message.document.file_id
        emoji = "📄"
    elif is_emoji:
        emoji = message.text

    await state.update_data(
        pending_file_id=file_id,
        pending_emoji=emoji,
        pending_set_name=set_name,
        pending_sticker_type=sticker_type,
    )

    await message.reply(
        l10n.get_text(message.from_user.language_code, "msg-what-to-do"),
        reply_markup=get_copy_menu(message.from_user.language_code),
    )


@router.callback_query(F.data.startswith("copy_step:"))
async def process_copy_step(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    step = callback.data.split(":")[1]
    data = await state.get_data()
    sticker_type = data.get("pending_sticker_type", "static")

    if step == "format":
        await callback.message.edit_text(
            l10n.get_text(callback.from_user.language_code, "msg-select-format"),
            reply_markup=get_format_selection(
                callback.from_user.language_code, sticker_type
            ),
        )
    elif step == "clone":
        # Check if it was a sticker to clone from
        file_id = data.get("pending_file_id")
        if not file_id:
            await callback.answer("❌ Can only clone from stickers.", show_alert=True)
            return

        # Need to find set name
        # Wait, get_file doesn't give set name. We need to use the message's sticker info if available.
        # But we saved file_id. Let's assume we have the set name if it was a sticker message.
        # In handle_incoming_media we can save the set_name.
        set_name = data.get("pending_set_name")
        if not set_name:
            await callback.answer(
                "❌ This sticker doesn't belong to a pack.", show_alert=True
            )
            return

        await state.update_data(source_set_name=set_name, cloning_mode=True)
        await callback.message.edit_text(
            l10n.get_text(callback.from_user.language_code, "msg-select-format"),
            reply_markup=get_format_selection(
                callback.from_user.language_code, sticker_type
            ),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("copy_fmt:"))
async def process_copy_format(callback: types.CallbackQuery, state: FSMContext):
    fmt = callback.data.split(":")[1]
    await state.update_data(target_format=fmt)
    data = await state.get_data()

    if data.get("cloning_mode"):
        await state.set_state(PackCreation.cloning_title)
        await callback.message.edit_text(
            l10n.get_text(callback.from_user.language_code, "prompt-title")
        )
        await callback.answer()
        return

    sticker_repo = container.resolve(StickerRepository)
    packs = await sticker_repo.get_by_creator(callback.from_user.id)

    # Filter packs by format (simplified: regular vs emoji)
    target_type = (
        "custom_emoji"
        if "emoji" in fmt
        else (
            "animated"
            if fmt == "animated"
            else ("video" if fmt == "video" else "regular")
        )
    )
    compatible_packs = [p for p in packs if p.set_type == target_type]

    if not compatible_packs:
        await callback.message.edit_text(
            l10n.get_text(callback.from_user.language_code, "msg-no-packs-create"),
            reply_markup=get_first_pack_keyboard(callback.from_user.language_code),
        )
    else:
        await callback.message.edit_text(
            l10n.get_text(callback.from_user.language_code, "msg-select-target"),
            reply_markup=get_user_packs_keyboard(
                compatible_packs, callback.from_user.language_code
            ),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("create_first:"))
async def start_first_pack(callback: types.CallbackQuery, state: FSMContext):
    sticker_type = callback.data.split(":")[1]
    await state.update_data(sticker_type=sticker_type)
    await state.set_state(PackCreation.waiting_name)

    await callback.message.edit_text(
        l10n.get_text(callback.from_user.language_code, "prompt-name"),
        reply_markup=get_cancel_keyboard(callback.from_user.language_code),
    )
    await callback.answer()


@router.callback_query(F.data == "copy_to")
async def start_copy_to(callback: types.CallbackQuery, state: FSMContext):
    sticker_repo = container.resolve(StickerRepository)
    packs = await sticker_repo.get_by_creator(callback.from_user.id)

    if not packs:
        await callback.message.edit_text(
            l10n.get_text(callback.from_user.language_code, "msg-no-packs-create"),
            reply_markup=get_first_pack_keyboard(callback.from_user.language_code),
        )
        return

    await callback.message.edit_text(
        l10n.get_text(callback.from_user.language_code, "msg-select-target"),
        reply_markup=get_user_packs_keyboard(packs, callback.from_user.language_code),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("target_pack:"))
async def process_copy_target(
    callback: types.CallbackQuery, state: FSMContext, bot: Bot
):
    pack_name = callback.data.split(":")[1]
    data = await state.get_data()

    # Check if we have a pending item
    file_id = data.get("pending_file_id")
    emoji = data.get("pending_emoji", "😀")

    if file_id or (emoji and not file_id):  # It might be just an emoji text
        # Perform one-time copy
        await add_item_to_pack(
            callback.message, pack_name, state, bot, file_id, emoji, is_callback=True
        )

    await callback.answer()


async def add_item_to_pack(
    message: types.Message,
    pack_name: str,
    state: FSMContext,
    bot: Bot,
    file_id=None,
    emoji="😀",
    is_callback=False,
):
    sticker_service = container.resolve(StickerService)
    pack_service = container.resolve(PackService)
    sticker_repo = container.resolve(StickerRepository)

    data = await state.get_data()
    target_format = data.get("target_format", "regular")

    # If not provided, get from message
    if not file_id and not is_callback:
        if message.sticker:
            file_id = message.sticker.file_id
            emoji = message.sticker.emoji or "😀"
        elif message.photo:
            file_id = message.photo[-1].file_id
            emoji = "🖼"
        elif message.video:
            file_id = message.video.file_id
            emoji = "🎥"
        elif message.animation:
            file_id = message.animation.file_id
            emoji = "✨"
        elif message.document:
            file_id = message.document.file_id
            emoji = "📄"
        elif message.text and len(message.text) <= 2:
            emoji = message.text

    if not file_id and not (message.text and len(message.text) <= 2):
        return

    # Get pack info to determine type
    pack_info = await sticker_repo.get_by_name(pack_name)
    if not pack_info:
        await message.answer("❌ Pack not found in database.")
        return

    try:
        if file_id:
            proc_msg = None
            if is_callback:
                await message.edit_text(
                    l10n.get_text(
                        message.from_user.language_code,
                        "msg-copying-one",
                        format=target_format,
                    )
                )
            else:
                proc_msg = await message.answer(
                    l10n.get_text(
                        message.from_user.language_code,
                        "msg-copying-one",
                        format=target_format,
                    )
                )

            # We use the selected format for processing, but the pack type for final storage
            file_data = await sticker_service.download_and_process(
                bot, file_id, target_format
            )

            # Detect format for InputSticker
            sticker_format = "static"
            if target_format in ["animated", "custom_emoji_anim"]:
                sticker_format = "animated"
            elif target_format in ["video", "custom_emoji_video"]:
                sticker_format = "video"

            input_sticker = sticker_service.create_input_sticker(
                file_data, emoji, sticker_format
            )
            await pack_service.add_sticker(message.chat.id, pack_name, input_sticker)

            msg_text = l10n.get_text(
                message.from_user.language_code,
                "item-added",
                count=pack_info.sticker_count + 1,
            )
            if is_callback:
                await message.edit_text(msg_text)
            elif proc_msg:
                await proc_msg.edit_text(msg_text)
        else:
            await message.answer("❌ Support for text-only items coming soon.")
    except Exception as e:
        logger.exception(f"Error in add_item_to_pack: {e}")
        err_msg = l10n.get_text(
            message.from_user.language_code, "err-generic", error=html.quote(str(e))
        )
        if is_callback:
            await message.edit_text(err_msg)
        else:
            await proc_msg.edit_text(err_msg)


@router.callback_query(F.data == "sticker_my_packs")
async def show_my_packs_for_mode(callback: types.CallbackQuery, state: FSMContext):
    sticker_repo = container.resolve(StickerRepository)
    packs = await sticker_repo.get_by_creator(callback.from_user.id)

    if not packs:
        await callback.message.edit_text(
            l10n.get_text(callback.from_user.language_code, "msg-no-packs-create"),
            reply_markup=get_first_pack_keyboard(callback.from_user.language_code),
        )
        return

    await callback.message.edit_text(
        l10n.get_text(callback.from_user.language_code, "btn-my-packs"),
        reply_markup=get_user_packs_keyboard(
            packs, callback.from_user.language_code, prefix="pack_details"
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pack_details:"))
async def show_pack_details(callback: types.CallbackQuery, state: FSMContext):
    pack_name = callback.data.split(":")[1]
    sticker_repo = container.resolve(StickerRepository)
    pack_info = await sticker_repo.get_by_name(pack_name)

    if not pack_info:
        await callback.answer("❌ Pack not found.", show_alert=True)
        return

    await callback.message.edit_text(
        l10n.get_text(
            callback.from_user.language_code, "msg-pack-manage", title=pack_info.title
        ),
        reply_markup=get_pack_manage_keyboard(
            callback.from_user.language_code, pack_name
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("activate_mode:"))
async def activate_copy_mode(callback: types.CallbackQuery, state: FSMContext):
    pack_name = callback.data.split(":")[1]
    sticker_repo = container.resolve(StickerRepository)
    pack_info = await sticker_repo.get_by_name(pack_name)

    await state.set_state(CopyMode.active)

    # Determine target format based on pack type
    target_fmt = "regular"
    if pack_info.set_type == "custom_emoji":
        target_fmt = "custom_emoji"
    elif pack_info.set_type == "animated":
        target_fmt = "animated"
    elif pack_info.set_type == "video":
        target_fmt = "video"

    await state.update_data(target_pack=pack_name, target_format=target_fmt)

    await callback.message.edit_text(
        l10n.get_text(
            callback.from_user.language_code, "msg-copy-mode-on", title=pack_info.title
        ),
        reply_markup=get_disable_keyboard(callback.from_user.language_code),
    )
    await callback.answer()


@router.callback_query(F.data == "copy_mode_off")
async def deactivate_copy_mode(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        l10n.get_text(callback.from_user.language_code, "msg-copy-mode-off")
    )
    await callback.answer()


@router.callback_query(F.data == "copy_back")
async def process_copy_back(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if data.get("pending_file_id") or data.get("pending_emoji"):
        await callback.message.edit_text(
            l10n.get_text(callback.from_user.language_code, "msg-what-to-do"),
            reply_markup=get_copy_menu(callback.from_user.language_code),
        )
    else:
        # Fallback to main menu if no pending item
        user_service = container.resolve(UserService)
        user = await user_service.get_or_create_user(
            callback.from_user.id,
            callback.from_user.username,
            callback.from_user.full_name,
            callback.from_user.language_code or "uk",
        )
        await callback.message.edit_text(
            l10n.get_text(user.language_code, "packs-menu"),
            reply_markup=get_packs_keyboard(user.language_code),
        )
    await callback.answer()


@router.callback_query(F.data == "sticker_done")
async def finish_creation(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    me = await bot.get_me()
    full_name = f"{data.get('pack_name_short')}_by_{me.username}"

    await callback.message.edit_text(
        l10n.get_text(
            callback.from_user.language_code,
            "create-success",
            title=data.get("pack_title"),
            name=full_name,
        ),
        reply_markup=get_open_pack_keyboard(
            callback.from_user.language_code, full_name
        ),
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "sticker_cancel")
async def cancel_creation(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.answer()
