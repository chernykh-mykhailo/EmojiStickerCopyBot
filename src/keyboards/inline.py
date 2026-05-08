from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.l10n import l10n


def get_packs_keyboard(locale: str):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=l10n.get_text(locale, "btn-create-regular"),
        callback_data="sticker_type:regular",
    )
    builder.button(
        text=l10n.get_text(locale, "btn-create-emoji"),
        callback_data="sticker_type:custom_emoji",
    )
    builder.button(
        text=l10n.get_text(locale, "btn-create-animated"),
        callback_data="sticker_type:animated",
    )
    builder.button(
        text=l10n.get_text(locale, "btn-create-video"),
        callback_data="sticker_type:video",
    )
    builder.button(
        text=l10n.get_text(locale, "btn-clone-pack"), callback_data="sticker_type:clone"
    )
    builder.button(
        text=l10n.get_text(locale, "btn-my-packs"), callback_data="sticker_my_packs"
    )
    builder.adjust(2)
    return builder.as_markup()


def get_cancel_keyboard(locale: str):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=l10n.get_text(locale, "btn-cancel"), callback_data="sticker_cancel"
    )
    return builder.as_markup()


def get_done_keyboard(locale: str):
    builder = InlineKeyboardBuilder()
    builder.button(text=l10n.get_text(locale, "btn-done"), callback_data="sticker_done")
    return builder.as_markup()


def get_copy_menu(locale: str, has_pack: bool = True):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=l10n.get_text(locale, "btn-copy-one"), callback_data="copy_step:format"
    )
    if has_pack:
        builder.button(
            text=l10n.get_text(locale, "btn-clone-all"), callback_data="copy_step:quick_clone"
        )
        builder.button(
            text=l10n.get_text(locale, "btn-clone-emoji"), callback_data="copy_step:quick_clone_emoji"
        )
    builder.button(
        text=l10n.get_text(locale, "btn-quick-create"), callback_data="copy_step:quick_create"
    )
    builder.button(
        text=l10n.get_text(locale, "btn-cancel"), callback_data="sticker_cancel"
    )
    builder.adjust(1)
    return builder.as_markup()


def get_format_selection(locale: str, sticker_type: str = "static"):
    builder = InlineKeyboardBuilder()

    if sticker_type == "static":
        builder.button(
            text=l10n.get_text(locale, "btn-fmt-original"),
            callback_data="copy_fmt:regular",
        )
        builder.button(
            text=l10n.get_text(locale, "btn-fmt-emoji"),
            callback_data="copy_fmt:custom_emoji",
        )
        builder.button(
            text=l10n.get_text(locale, "btn-fmt-emoji-nobg"),
            callback_data="copy_fmt:emoji_nobg",
        )
    elif sticker_type == "animated":
        builder.button(
            text=l10n.get_text(locale, "btn-fmt-original"),
            callback_data="copy_fmt:animated",
        )
        builder.button(
            text=l10n.get_text(locale, "btn-fmt-emoji"),
            callback_data="copy_fmt:custom_emoji_anim",
        )
    elif sticker_type == "video":
        builder.button(
            text=l10n.get_text(locale, "btn-fmt-original"),
            callback_data="copy_fmt:video",
        )
        builder.button(
            text=l10n.get_text(locale, "btn-fmt-emoji"),
            callback_data="copy_fmt:custom_emoji_video",
        )

    builder.button(text=l10n.get_text(locale, "btn-back"), callback_data="copy_back")
    builder.adjust(1)
    return builder.as_markup()


def get_first_pack_keyboard(locale: str):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=l10n.get_text(locale, "btn-create-first-regular"),
        callback_data="create_first:regular",
    )
    builder.button(
        text=l10n.get_text(locale, "btn-create-first-emoji"),
        callback_data="create_first:custom_emoji",
    )
    builder.button(
        text=l10n.get_text(locale, "btn-cancel"), callback_data="sticker_cancel"
    )
    builder.adjust(1)
    return builder.as_markup()


def get_user_packs_keyboard(packs: list, locale: str, prefix: str = "target_pack"):
    builder = InlineKeyboardBuilder()
    for pack in packs:
        builder.button(text=pack.title, callback_data=f"{prefix}:{pack.name}")

    builder.button(
        text=l10n.get_text(locale, "btn-create-new"), callback_data="create_new_from_copy"
    )

    builder.button(text=l10n.get_text(locale, "btn-back"), callback_data="copy_back")
    builder.button(
        text=l10n.get_text(locale, "btn-cancel"), callback_data="sticker_cancel"
    )
    builder.adjust(1)
    return builder.as_markup()


def get_disable_keyboard(locale: str):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=l10n.get_text(locale, "btn-disable"), callback_data="copy_mode_off"
    )
    return builder.as_markup()


def get_open_pack_keyboard(locale: str, name: str):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=l10n.get_text(locale, "btn-open-pack"),
        url=f"https://t.me/addstickers/{name}",
    )
    return builder.as_markup()


def get_pack_manage_keyboard(locale: str, name: str):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=l10n.get_text(locale, "btn-open-pack"),
        url=f"https://t.me/addstickers/{name}",
    )
    builder.button(
        text=l10n.get_text(locale, "btn-copy-to-this"),
        callback_data=f"activate_mode:{name}",
    )
    builder.button(
        text=l10n.get_text(locale, "btn-remove-from-list"),
        callback_data=f"remove_pack:{name}",
    )
    builder.button(
        text=l10n.get_text(locale, "btn-back"), callback_data="sticker_my_packs"
    )
    builder.adjust(1)
    return builder.as_markup()


def get_title_suggestions_keyboard(locale: str, suggestions: list[str]):
    builder = InlineKeyboardBuilder()
    for suggestion in suggestions:
        builder.button(text=suggestion, callback_data=f"suggested_title:{suggestion}")

    builder.button(
        text=l10n.get_text(locale, "btn-cancel"), callback_data="sticker_cancel"
    )
    builder.adjust(2)
    return builder.as_markup()
