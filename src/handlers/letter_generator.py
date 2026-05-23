import re
import logging
from aiogram import Router, F, Bot, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.letter_pack_creator import create_letter_pack, ALPHABETS

logger = logging.getLogger(__name__)
router = Router()

class LetterGeneratorState(StatesGroup):
    choosing_lang = State()
    choosing_bg_style = State()
    choosing_bg_color = State()
    choosing_font = State()
    choosing_fill_type = State()
    choosing_text_color = State()
    choosing_gradient_start = State()
    choosing_gradient_end = State()
    choosing_outline_width = State()
    choosing_outline_color = State()
    waiting_title = State()
    waiting_name = State()

COLOR_MAP = {
    "red": (230, 50, 50),
    "orange": (255, 149, 0),
    "yellow": (255, 204, 0),
    "green": (52, 199, 89),
    "blue": (0, 122, 255),
    "purple": (175, 82, 222),
    "black": (0, 0, 0),
    "white": (255, 255, 255)
}

LOCALIZATION = {
    "uk": {
        "start_generator": "✨ <b>Генератор емодзі-літер</b>\n\nЦей інструмент дозволяє створити стікерпак з кастомними емодзі-літерами (A-Z або А-Я) з обраним шрифтом, кольорами та стилем.\n\nОберіть мову літер:",
        "choose_bg_style": "Оберіть стиль фону:",
        "choose_bg_color": "Оберіть колір фону:\n(Ви можете обрати з готових або надіслати HEX-код в чат, наприклад: <code>#FF5733</code>)",
        "choose_font": "Оберіть шрифт:",
        "choose_fill_type": "Оберіть тип заливки літери:",
        "choose_text_color": "Оберіть колір літери:\n(Ви можете обрати з готових або надіслати HEX-код в чат, наприклад: <code>#FFFFFF</code>)",
        "choose_gradient_start": "Оберіть стартовий колір градієнту:\n(Ви можете обрати з готових або надіслати HEX-код в чат, наприклад: <code>#FF0000</code>)",
        "choose_gradient_end": "Оберіть кінцевий колір градієнту:\n(Ви можете обрати з готових або надіслати HEX-код в чат, наприклад: <code>#FFFF00</code>)",
        "choose_outline_width": "Оберіть товщину обведення літери:",
        "choose_outline_color": "Оберіть колір обведення літери:\n(Ви можете обрати з готових або надіслати HEX-код в чат, наприклад: <code>#000000</code>)",
        "waiting_title": "Введіть <b>назву</b> для свого нового емодзі-паку літер:\n(Наприклад: <i>Pixel Yellow letters</i>)",
        "waiting_name": "Тепер надішліть <b>коротку назву</b> (slug) для посилання (тільки латиниця та цифри):",
        "generating": "⏳ <b>Початок генерації емодзі-паку...</b>\nЦе займе деякий час (15-30 секунд), оскільки створюється повний алфавіт. Будь ласка, зачекайте.",
        "success": "✅ <b>Кастомний емодзі-пак літер успішно створено!</b>\n\nНазва: <b>{title}</b>\nПосилання: <a href=\"https://t.me/addstickers/{name}\">Додати емодзі</a>",
        "error": "❌ Сталася помилка при створенні паку: {error}",
        "btn_cancel": "❌ Скасувати",
        "btn_back": "🔙 Назад",
        "invalid_hex": "❌ Некоректний HEX-код. Будь ласка, введіть код у форматі <code>#FFFFFF</code> або оберіть зі списку:",
        "invalid_name": "❌ Некоректна коротка назва. Використовуйте лише латинські літери та цифри.",
        "prompt_custom_hex": "Введіть свій HEX-код кольору (наприклад, <code>#3AB4F2</code>):",
        "bg_styles": {
            "transparent": "👤 Без фону (прозорий)",
            "circle": "🔴 Круглий фон",
            "square": "🟥 Квадратний фон",
            "emoji_red": "🅰️ Червоний квадрат (Emoji-like)",
            "wordle_grey": "⬜ Сірий тайл (Wordle-like)",
            "wordle_yellow": "🟨 Жовтий тайл (Wordle-like)",
            "wordle_green": "🟩 Зелений тайл (Wordle-like)"
        },
        "fonts": {
            "arial": "Arial",
            "arial_black": "Arial Black (Bold)",
            "impact": "Impact",
            "comic_sans": "Comic Sans",
            "segoe_ui": "Segoe UI",
            "georgia": "Georgia",
            "times": "Times New Roman",
            "courier": "Courier"
        },
        "fill_types": {
            "solid": "🎨 Один колір",
            "gradient": "🌈 Градієнт"
        },
        "colors": {
            "red": "🔴 Червоний",
            "orange": "🟠 Помаранчевий",
            "yellow": "🟡 Жовтий",
            "green": "🟢 Зелений",
            "blue": "🔵 Синій",
            "purple": "🟣 Фіолетовий",
            "black": "⚫ Чорний",
            "white": "⚪ Білий",
            "custom": "🎨 Свій HEX"
        },
        "outline_widths": {
            "0": "❌ Без обведення",
            "3": "Тонке (3px)",
            "6": "Середнє (6px)",
            "10": "Товсте (10px)"
        }
    },
    "en": {
        "start_generator": "✨ <b>Letter Emoji Generator</b>\n\nThis tool creates a custom emoji pack containing alphabet letters (A-Z or А-Я) with your custom font, colors, and styling.\n\nChoose language of the letters:",
        "choose_bg_style": "Choose background style:",
        "choose_bg_color": "Choose background color:\n(Select below or send a HEX code in chat, e.g. <code>#FF5733</code>)",
        "choose_font": "Choose font:",
        "choose_fill_type": "Choose letter fill type:",
        "choose_text_color": "Choose text color:\n(Select below or send a HEX code in chat, e.g. <code>#FFFFFF</code>)",
        "choose_gradient_start": "Choose gradient start color:\n(Select below or send a HEX code in chat, e.g. <code>#FF0000</code>)",
        "choose_gradient_end": "Choose gradient end color:\n(Select below or send a HEX code in chat, e.g. <code>#FFFF00</code>)",
        "choose_outline_width": "Choose outline width:",
        "choose_outline_color": "Choose outline color:\n(Select below or send a HEX code in chat, e.g. <code>#000000</code>)",
        "waiting_title": "Enter a <b>title</b> for your new letter emoji pack:\n(E.g., <i>Pixel Yellow Letters</i>)",
        "waiting_name": "Now enter a <b>short name</b> (slug) for the pack link (English letters/digits only):",
        "generating": "⏳ <b>Generating emoji pack...</b>\nThis might take 15-30 seconds to generate the full alphabet. Please wait.",
        "success": "✅ <b>Custom letter emoji pack created successfully!</b>\n\nTitle: <b>{title}</b>\nLink: <a href=\"https://t.me/addstickers/{name}\">Add Emoji Pack</a>",
        "error": "❌ Error creating pack: {error}",
        "btn_cancel": "❌ Cancel",
        "btn_back": "🔙 Back",
        "invalid_hex": "❌ Invalid HEX code. Please enter a hex color in format <code>#FFFFFF</code> or choose from below:",
        "invalid_name": "❌ Invalid short name. Use alphanumeric characters only.",
        "prompt_custom_hex": "Enter your custom HEX color code (e.g. <code>#3AB4F2</code>):",
        "bg_styles": {
            "transparent": "👤 Transparent (no background)",
            "circle": "🔴 Circle background",
            "square": "🟥 Square background",
            "emoji_red": "🅰️ Red Square (Emoji-like)",
            "wordle_grey": "⬜ Grey Tile (Wordle-like)",
            "wordle_yellow": "🟨 Yellow Tile (Wordle-like)",
            "wordle_green": "🟩 Green Tile (Wordle-like)"
        },
        "fonts": {
            "arial": "Arial",
            "arial_black": "Arial Black (Bold)",
            "impact": "Impact",
            "comic_sans": "Comic Sans",
            "segoe_ui": "Segoe UI",
            "georgia": "Georgia",
            "times": "Times New Roman",
            "courier": "Courier"
        },
        "fill_types": {
            "solid": "🎨 Solid Color",
            "gradient": "🌈 Gradient"
        },
        "colors": {
            "red": "🔴 Red",
            "orange": "Orange",
            "yellow": "🟡 Yellow",
            "green": "🟢 Green",
            "blue": "🔵 Blue",
            "purple": "🟣 Purple",
            "black": "⚫ Black",
            "white": "⚪ White",
            "custom": "🎨 Custom HEX"
        },
        "outline_widths": {
            "0": "❌ No Outline",
            "3": "Thin (3px)",
            "6": "Medium (6px)",
            "10": "Thick (10px)"
        }
    }
}

def get_txt(locale: str, key: str, **kwargs) -> str:
    loc = locale if locale in LOCALIZATION else "en"
    text = LOCALIZATION[loc].get(key, key)
    if isinstance(text, str):
        return text.format(**kwargs)
    return text

def hex_to_rgb(hex_str: str) -> tuple[int, int, int] | None:
    hex_str = hex_str.lstrip('#').strip()
    if len(hex_str) == 3:
        hex_str = ''.join([c*2 for c in hex_str])
    if len(hex_str) != 6:
        return None
    try:
        return int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
    except ValueError:
        return None

def parse_color(color_val: str) -> tuple[int, int, int]:
    if color_val in COLOR_MAP:
        return COLOR_MAP[color_val]
    parsed = hex_to_rgb(color_val)
    if parsed:
        return parsed
    return (255, 255, 255)

# --- Keyboards ---

def get_lang_kb(locale: str):
    builder = InlineKeyboardBuilder()
    builder.button(text="🇺🇦 Українська", callback_data="lg_lang:uk")
    builder.button(text="🇬🇧 English", callback_data="lg_lang:en")
    builder.button(text=get_txt(locale, "btn_cancel"), callback_data="lg_cancel")
    builder.adjust(2, 1)
    return builder.as_markup()

def get_bg_style_kb(locale: str):
    builder = InlineKeyboardBuilder()
    styles = get_txt(locale, "bg_styles")
    for style, name in styles.items():
        builder.button(text=name, callback_data=f"lg_bg_style:{style}")
    builder.button(text=get_txt(locale, "btn_cancel"), callback_data="lg_cancel")
    builder.adjust(1)
    return builder.as_markup()

def get_color_kb(locale: str, callback_prefix: str):
    builder = InlineKeyboardBuilder()
    colors = get_txt(locale, "colors")
    for color_id, color_name in colors.items():
        builder.button(text=color_name, callback_data=f"{callback_prefix}:{color_id}")
    builder.button(text=get_txt(locale, "btn_cancel"), callback_data="lg_cancel")
    builder.adjust(3, 3, 3, 1)
    return builder.as_markup()

def get_font_kb(locale: str):
    builder = InlineKeyboardBuilder()
    fonts = get_txt(locale, "fonts")
    for font_id, font_name in fonts.items():
        builder.button(text=font_name, callback_data=f"lg_font:{font_id}")
    builder.button(text=get_txt(locale, "btn_cancel"), callback_data="lg_cancel")
    builder.adjust(2)
    return builder.as_markup()

def get_fill_type_kb(locale: str):
    builder = InlineKeyboardBuilder()
    fill_types = get_txt(locale, "fill_types")
    for fill_id, fill_name in fill_types.items():
        builder.button(text=fill_name, callback_data=f"lg_fill:{fill_id}")
    builder.button(text=get_txt(locale, "btn_cancel"), callback_data="lg_cancel")
    builder.adjust(2, 1)
    return builder.as_markup()

def get_outline_width_kb(locale: str):
    builder = InlineKeyboardBuilder()
    widths = get_txt(locale, "outline_widths")
    for w_id, w_name in widths.items():
        builder.button(text=w_name, callback_data=f"lg_outline_w:{w_id}")
    builder.button(text=get_txt(locale, "btn_cancel"), callback_data="lg_cancel")
    builder.adjust(1)
    return builder.as_markup()

def get_suggested_name_kb(locale: str, suggested_name: str):
    builder = InlineKeyboardBuilder()
    builder.button(text=suggested_name, callback_data=f"lg_suggested_name:{suggested_name}")
    builder.button(text=get_txt(locale, "btn_cancel"), callback_data="lg_cancel")
    builder.adjust(1)
    return builder.as_markup()

def get_cancel_kb(locale: str):
    builder = InlineKeyboardBuilder()
    builder.button(text=get_txt(locale, "btn_cancel"), callback_data="lg_cancel")
    return builder.as_markup()

# --- Handlers ---

@router.message(Command("letterpack"))
async def cmd_letterpack(message: types.Message, state: FSMContext):
    await state.clear()
    locale = message.from_user.language_code or "uk"
    await state.set_state(LetterGeneratorState.choosing_lang)
    await message.answer(
        get_txt(locale, "start_generator"),
        reply_markup=get_lang_kb(locale),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "lg_start")
async def cb_lg_start(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    locale = callback.from_user.language_code or "uk"
    await state.set_state(LetterGeneratorState.choosing_lang)
    await callback.message.edit_text(
        get_txt(locale, "start_generator"),
        reply_markup=get_lang_kb(locale),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "lg_cancel")
async def process_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.answer()

@router.callback_query(LetterGeneratorState.choosing_lang, F.data.startswith("lg_lang:"))
async def select_lang(callback: types.CallbackQuery, state: FSMContext):
    lang = callback.data.split(":")[1]
    await state.update_data(lang=lang)
    locale = callback.from_user.language_code or "uk"
    await state.set_state(LetterGeneratorState.choosing_bg_style)
    await callback.message.edit_text(
        get_txt(locale, "choose_bg_style"),
        reply_markup=get_bg_style_kb(locale),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(LetterGeneratorState.choosing_bg_style, F.data.startswith("lg_bg_style:"))
async def select_bg_style(callback: types.CallbackQuery, state: FSMContext):
    style = callback.data.split(":")[1]
    await state.update_data(bg_style=style)
    locale = callback.from_user.language_code or "uk"

    if style == "emoji_red":
        await state.update_data(bg_color="red", font_name="arial_black")
        # For red square, we skip bg color and custom font, using standard settings
        await state.set_state(LetterGeneratorState.choosing_fill_type)
        await callback.message.edit_text(
            get_txt(locale, "choose_fill_type"),
            reply_markup=get_fill_type_kb(locale),
            parse_mode="HTML"
        )
    elif style in ["wordle_grey", "wordle_yellow", "wordle_green"]:
        # Auto-set style colors and font settings for Wordle
        color_map = {
            "wordle_grey": "#a2aabf",
            "wordle_yellow": "#facc15",
            "wordle_green": "#22c55e"
        }
        await state.update_data(
            bg_color=color_map[style],
            font_name="arial_black",
            fill_type="solid",
            text_color="#000000",
            outline_width="0"
        )
        # Skip straight to title & name!
        await state.set_state(LetterGeneratorState.waiting_title)
        await callback.message.edit_text(
            get_txt(locale, "waiting_title"),
            reply_markup=get_cancel_kb(locale),
            parse_mode="HTML"
        )
    elif style == "transparent":
        await state.update_data(bg_color="transparent")
        await state.set_state(LetterGeneratorState.choosing_font)
        await callback.message.edit_text(
            get_txt(locale, "choose_font"),
            reply_markup=get_font_kb(locale),
            parse_mode="HTML"
        )
    else:
        await state.set_state(LetterGeneratorState.choosing_bg_color)
        await callback.message.edit_text(
            get_txt(locale, "choose_bg_color"),
            reply_markup=get_color_kb(locale, "lg_bg_color"),
            parse_mode="HTML"
        )
    await callback.answer()

@router.callback_query(LetterGeneratorState.choosing_bg_color, F.data.startswith("lg_bg_color:"))
async def select_bg_color_cb(callback: types.CallbackQuery, state: FSMContext):
    color = callback.data.split(":")[1]
    locale = callback.from_user.language_code or "uk"
    if color == "custom":
        await callback.message.edit_text(
            get_txt(locale, "prompt_custom_hex"),
            reply_markup=get_cancel_kb(locale),
            parse_mode="HTML"
        )
    else:
        await state.update_data(bg_color=color)
        await state.set_state(LetterGeneratorState.choosing_font)
        await callback.message.edit_text(
            get_txt(locale, "choose_font"),
            reply_markup=get_font_kb(locale),
            parse_mode="HTML"
        )
    await callback.answer()

@router.message(LetterGeneratorState.choosing_bg_color, F.text)
async def select_bg_color_txt(message: types.Message, state: FSMContext):
    locale = message.from_user.language_code or "uk"
    color = message.text.strip()
    if not re.match(r"^#?[a-fA-F0-9]{6}$", color) and not re.match(r"^#?[a-fA-F0-9]{3}$", color):
        await message.reply(
            get_txt(locale, "invalid_hex"),
            reply_markup=get_color_kb(locale, "lg_bg_color"),
            parse_mode="HTML"
        )
        return
    await state.update_data(bg_color=color)
    await state.set_state(LetterGeneratorState.choosing_font)
    await message.answer(
        get_txt(locale, "choose_font"),
        reply_markup=get_font_kb(locale),
        parse_mode="HTML"
    )

@router.callback_query(LetterGeneratorState.choosing_font, F.data.startswith("lg_font:"))
async def select_font(callback: types.CallbackQuery, state: FSMContext):
    font = callback.data.split(":")[1]
    await state.update_data(font_name=font)
    locale = callback.from_user.language_code or "uk"
    await state.set_state(LetterGeneratorState.choosing_fill_type)
    await callback.message.edit_text(
        get_txt(locale, "choose_fill_type"),
        reply_markup=get_fill_type_kb(locale),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(LetterGeneratorState.choosing_fill_type, F.data.startswith("lg_fill:"))
async def select_fill_type(callback: types.CallbackQuery, state: FSMContext):
    fill_type = callback.data.split(":")[1]
    await state.update_data(fill_type=fill_type)
    locale = callback.from_user.language_code or "uk"
    if fill_type == "solid":
        await state.set_state(LetterGeneratorState.choosing_text_color)
        await callback.message.edit_text(
            get_txt(locale, "choose_text_color"),
            reply_markup=get_color_kb(locale, "lg_text_color"),
            parse_mode="HTML"
        )
    else:
        await state.set_state(LetterGeneratorState.choosing_gradient_start)
        await callback.message.edit_text(
            get_txt(locale, "choose_gradient_start"),
            reply_markup=get_color_kb(locale, "lg_grad_start"),
            parse_mode="HTML"
        )
    await callback.answer()

# Solid Text Color
@router.callback_query(LetterGeneratorState.choosing_text_color, F.data.startswith("lg_text_color:"))
async def select_text_color_cb(callback: types.CallbackQuery, state: FSMContext):
    color = callback.data.split(":")[1]
    locale = callback.from_user.language_code or "uk"
    if color == "custom":
        await callback.message.edit_text(
            get_txt(locale, "prompt_custom_hex"),
            reply_markup=get_cancel_kb(locale),
            parse_mode="HTML"
        )
    else:
        await state.update_data(text_color=color)
        await state.set_state(LetterGeneratorState.choosing_outline_width)
        await callback.message.edit_text(
            get_txt(locale, "choose_outline_width"),
            reply_markup=get_outline_width_kb(locale),
            parse_mode="HTML"
        )
    await callback.answer()

@router.message(LetterGeneratorState.choosing_text_color, F.text)
async def select_text_color_txt(message: types.Message, state: FSMContext):
    locale = message.from_user.language_code or "uk"
    color = message.text.strip()
    if not re.match(r"^#?[a-fA-F0-9]{6}$", color) and not re.match(r"^#?[a-fA-F0-9]{3}$", color):
        await message.reply(
            get_txt(locale, "invalid_hex"),
            reply_markup=get_color_kb(locale, "lg_text_color"),
            parse_mode="HTML"
        )
        return
    await state.update_data(text_color=color)
    await state.set_state(LetterGeneratorState.choosing_outline_width)
    await message.answer(
        get_txt(locale, "choose_outline_width"),
        reply_markup=get_outline_width_kb(locale),
        parse_mode="HTML"
    )

# Gradient Start
@router.callback_query(LetterGeneratorState.choosing_gradient_start, F.data.startswith("lg_grad_start:"))
async def select_grad_start_cb(callback: types.CallbackQuery, state: FSMContext):
    color = callback.data.split(":")[1]
    locale = callback.from_user.language_code or "uk"
    if color == "custom":
        await callback.message.edit_text(
            get_txt(locale, "prompt_custom_hex"),
            reply_markup=get_cancel_kb(locale),
            parse_mode="HTML"
        )
    else:
        await state.update_data(grad_start=color)
        await state.set_state(LetterGeneratorState.choosing_gradient_end)
        await callback.message.edit_text(
            get_txt(locale, "choose_gradient_end"),
            reply_markup=get_color_kb(locale, "lg_grad_end"),
            parse_mode="HTML"
        )
    await callback.answer()

@router.message(LetterGeneratorState.choosing_gradient_start, F.text)
async def select_grad_start_txt(message: types.Message, state: FSMContext):
    locale = message.from_user.language_code or "uk"
    color = message.text.strip()
    if not re.match(r"^#?[a-fA-F0-9]{6}$", color) and not re.match(r"^#?[a-fA-F0-9]{3}$", color):
        await message.reply(
            get_txt(locale, "invalid_hex"),
            reply_markup=get_color_kb(locale, "lg_grad_start"),
            parse_mode="HTML"
        )
        return
    await state.update_data(grad_start=color)
    await state.set_state(LetterGeneratorState.choosing_gradient_end)
    await message.answer(
        get_txt(locale, "choose_gradient_end"),
        reply_markup=get_color_kb(locale, "lg_grad_end"),
        parse_mode="HTML"
    )

# Gradient End
@router.callback_query(LetterGeneratorState.choosing_gradient_end, F.data.startswith("lg_grad_end:"))
async def select_grad_end_cb(callback: types.CallbackQuery, state: FSMContext):
    color = callback.data.split(":")[1]
    locale = callback.from_user.language_code or "uk"
    if color == "custom":
        await callback.message.edit_text(
            get_txt(locale, "prompt_custom_hex"),
            reply_markup=get_cancel_kb(locale),
            parse_mode="HTML"
        )
    else:
        await state.update_data(grad_end=color)
        await state.set_state(LetterGeneratorState.choosing_outline_width)
        await callback.message.edit_text(
            get_txt(locale, "choose_outline_width"),
            reply_markup=get_outline_width_kb(locale),
            parse_mode="HTML"
        )
    await callback.answer()

@router.message(LetterGeneratorState.choosing_gradient_end, F.text)
async def select_grad_end_txt(message: types.Message, state: FSMContext):
    locale = message.from_user.language_code or "uk"
    color = message.text.strip()
    if not re.match(r"^#?[a-fA-F0-9]{6}$", color) and not re.match(r"^#?[a-fA-F0-9]{3}$", color):
        await message.reply(
            get_txt(locale, "invalid_hex"),
            reply_markup=get_color_kb(locale, "lg_grad_end"),
            parse_mode="HTML"
        )
        return
    await state.update_data(grad_end=color)
    await state.set_state(LetterGeneratorState.choosing_outline_width)
    await message.answer(
        get_txt(locale, "choose_outline_width"),
        reply_markup=get_outline_width_kb(locale),
        parse_mode="HTML"
    )

# Outline Width
@router.callback_query(LetterGeneratorState.choosing_outline_width, F.data.startswith("lg_outline_w:"))
async def select_outline_width(callback: types.CallbackQuery, state: FSMContext):
    w = callback.data.split(":")[1]
    await state.update_data(outline_width=w)
    locale = callback.from_user.language_code or "uk"
    if w == "0":
        await state.set_state(LetterGeneratorState.waiting_title)
        await callback.message.edit_text(
            get_txt(locale, "waiting_title"),
            reply_markup=get_cancel_kb(locale),
            parse_mode="HTML"
        )
    else:
        await state.set_state(LetterGeneratorState.choosing_outline_color)
        await callback.message.edit_text(
            get_txt(locale, "choose_outline_color"),
            reply_markup=get_color_kb(locale, "lg_outline_color"),
            parse_mode="HTML"
        )
    await callback.answer()

# Outline Color
@router.callback_query(LetterGeneratorState.choosing_outline_color, F.data.startswith("lg_outline_color:"))
async def select_outline_color_cb(callback: types.CallbackQuery, state: FSMContext):
    color = callback.data.split(":")[1]
    locale = callback.from_user.language_code or "uk"
    if color == "custom":
        await callback.message.edit_text(
            get_txt(locale, "prompt_custom_hex"),
            reply_markup=get_cancel_kb(locale),
            parse_mode="HTML"
        )
    else:
        await state.update_data(outline_color=color)
        await state.set_state(LetterGeneratorState.waiting_title)
        await callback.message.edit_text(
            get_txt(locale, "waiting_title"),
            reply_markup=get_cancel_kb(locale),
            parse_mode="HTML"
        )
    await callback.answer()

@router.message(LetterGeneratorState.choosing_outline_color, F.text)
async def select_outline_color_txt(message: types.Message, state: FSMContext):
    locale = message.from_user.language_code or "uk"
    color = message.text.strip()
    if not re.match(r"^#?[a-fA-F0-9]{6}$", color) and not re.match(r"^#?[a-fA-F0-9]{3}$", color):
        await message.reply(
            get_txt(locale, "invalid_hex"),
            reply_markup=get_color_kb(locale, "lg_outline_color"),
            parse_mode="HTML"
        )
        return
    await state.update_data(outline_color=color)
    await state.set_state(LetterGeneratorState.waiting_title)
    await message.answer(
        get_txt(locale, "waiting_title"),
        reply_markup=get_cancel_kb(locale),
        parse_mode="HTML"
    )

# Title
@router.message(LetterGeneratorState.waiting_title, F.text)
async def select_title(message: types.Message, state: FSMContext):
    title = message.text.strip()
    await state.update_data(pack_title=title)
    locale = message.from_user.language_code or "uk"

    # Make a suggested slug name
    suggested = re.sub(r"[^a-zA-Z0-9_]", "", title.lower())
    # Ensure it starts with a letter, if not, prepend 'pack'
    if not suggested or not suggested[0].isalpha():
        suggested = "pack_" + suggested

    await state.set_state(LetterGeneratorState.waiting_name)
    await message.answer(
        get_txt(locale, "waiting_name"),
        reply_markup=get_suggested_name_kb(locale, suggested),
        parse_mode="HTML"
    )

# Short Name (slug)
@router.callback_query(LetterGeneratorState.waiting_name, F.data.startswith("lg_suggested_name:"))
async def select_name_cb(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    slug = callback.data.split(":")[1]
    await generate_and_create(callback, state, bot, slug)
    await callback.answer()

@router.message(LetterGeneratorState.waiting_name, F.text)
async def select_name_txt(message: types.Message, state: FSMContext, bot: Bot):
    slug = message.text.strip()
    locale = message.from_user.language_code or "uk"
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", slug):
        await message.reply(
            get_txt(locale, "invalid_name"),
            reply_markup=get_cancel_kb(locale),
            parse_mode="HTML"
        )
        return
    await generate_and_create(message, state, bot, slug)

# --- Generator Execution ---

async def generate_and_create(event: types.Message | types.CallbackQuery, state: FSMContext, bot: Bot, name_short: str):
    locale = event.from_user.language_code or "uk"
    reply_to = event.message if isinstance(event, types.CallbackQuery) else event

    # Tell user generator started
    status_msg = await reply_to.reply(
        get_txt(locale, "generating"),
        parse_mode="HTML"
    )

    data = await state.get_data()
    lang = data.get("lang", "uk")
    title = data.get("pack_title", "Custom Letters")

    # Reconstruct Pillow arguments
    bg_style = data.get("bg_style", "transparent")
    bg_color_raw = data.get("bg_color", "black")
    
    # Map Wordle styles to rounded rectangle (square) style for PIL drawing
    if bg_style in ["wordle_grey", "wordle_yellow", "wordle_green"]:
        pillow_bg_style = "square"
    else:
        pillow_bg_style = bg_style
        
    bg_color = parse_color(bg_color_raw) if pillow_bg_style in ["circle", "square"] else (0, 0, 0, 0)

    font_name = data.get("font_name", "arial_black")

    fill_type = data.get("fill_type", "solid")
    if fill_type == "gradient":
        grad_start = parse_color(data.get("grad_start", "red"))
        grad_end = parse_color(data.get("grad_end", "yellow"))
        text_color = (grad_start, grad_end)
    else:
        text_color = parse_color(data.get("text_color", "white"))

    outline_width = int(data.get("outline_width", 0))
    outline_color = parse_color(data.get("outline_color", "black")) if outline_width > 0 else (0, 0, 0)

    style_options = {
        "bg_style": pillow_bg_style,
        "bg_color": bg_color,
        "font_name": font_name,
        "font_size": 75 if font_name == "impact" else 70,
        "text_color": text_color,
        "outline_width": outline_width,
        "outline_color": outline_color,
    }

    try:
        # Create pack via utils.letter_pack_creator
        full_name = await create_letter_pack(
            bot=bot,
            user_id=event.from_user.id,
            name_short=name_short,
            title=title,
            lang=lang,
            style_options=style_options,
        )

        # Attempt to save to local database if DB service / DI exists
        try:
            from core.di import container
            from database.repositories.sticker_repo import StickerRepository
            sticker_repo = container.resolve(StickerRepository)
            alphabet = ALPHABETS.get(lang.lower(), ALPHABETS["uk"])
            me = await bot.get_me()
            full_db_name = f"{name_short}_by_{me.username}"
            full_db_title = f"{title} by @{me.username}"

            await sticker_repo.create(
                name=full_db_name,
                title=full_db_title,
                creator_id=event.from_user.id,
                set_type="custom_emoji",
                sticker_count=len(alphabet),
            )
            logger.info(f"Registered generated pack {full_db_name} in database.")
        except Exception as db_err:
            logger.warning(f"Could not register pack in database (ignoring): {db_err}")

        # Edit status msg with success link
        await status_msg.edit_text(
            get_txt(locale, "success", title=title, name=full_name),
            parse_mode="HTML"
        )
        await state.clear()

    except Exception as e:
        logger.exception(f"Error generating letter pack: {e}")
        await status_msg.edit_text(
            get_txt(locale, "error", error=str(e)),
            parse_mode="HTML"
        )
