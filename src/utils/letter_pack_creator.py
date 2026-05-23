import io
import re
import os
import logging
from PIL import Image, ImageDraw, ImageFont
from aiogram import Bot
from aiogram.types import BufferedInputFile, InputSticker

logger = logging.getLogger(__name__)

ALPHABETS = {
    "en": [
        "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M",
        "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"
    ],
    "uk": [
        "А", "Б", "В", "Г", "Ґ", "Д", "Е", "Є", "Ж", "З", "И", "І", "Ї",
        "Й", "К", "Л", "М", "Н", "О", "П", "Р", "С", "Т", "У", "Ф", "Х",
        "Ц", "Ч", "Ш", "Щ", "Ь", "Ю", "Я"
    ]
}

def get_font_path(font_name: str) -> str:
    """Find system font path supporting Windows and Linux (Docker)"""
    font_name = font_name.lower()
    
    # Define filenames for Windows and Linux fallbacks
    font_configs = {
        "arial": {
            "win": "arial.ttf",
            "linux": "liberation/LiberationSans-Regular.ttf",
            "linux_fallback": "dejavu/DejaVuSans.ttf"
        },
        "arial_black": {
            "win": "ariblk.ttf",
            "linux": "liberation/LiberationSans-Bold.ttf",
            "linux_fallback": "dejavu/DejaVuSans-Bold.ttf"
        },
        "impact": {
            "win": "impact.ttf",
            "linux": "dejavu/DejaVuSans-Bold.ttf",  # Heavy fallback
            "linux_fallback": "liberation/LiberationSans-Bold.ttf"
        },
        "comic_sans": {
            "win": "comic.ttf",
            "linux": "dejavu/DejaVuSans.ttf",
            "linux_fallback": "liberation/LiberationSans-Regular.ttf"
        },
        "segoe_ui": {
            "win": "segoeuib.ttf",
            "linux": "liberation/LiberationSans-Bold.ttf",
            "linux_fallback": "dejavu/DejaVuSans-Bold.ttf"
        },
        "georgia": {
            "win": "georgiab.ttf",
            "linux": "liberation/LiberationSerif-Bold.ttf",
            "linux_fallback": "dejavu/DejaVuSerif-Bold.ttf"
        },
        "times": {
            "win": "times.ttf",
            "linux": "liberation/LiberationSerif-Regular.ttf",
            "linux_fallback": "dejavu/DejaVuSerif.ttf"
        },
        "courier": {
            "win": "cour.ttf",
            "linux": "liberation/LiberationMono-Regular.ttf",
            "linux_fallback": "dejavu/DejaVuSansMono.ttf"
        }
    }
    
    cfg = font_configs.get(font_name, font_configs["arial"])
    
    # 1. Check local './fonts/' folder first (if user puts fonts manually)
    local_path = os.path.join("fonts", cfg["win"])
    if os.path.exists(local_path):
        return local_path
        
    # 2. Check Windows Fonts path
    win_root = os.environ.get("SystemRoot", "C:\\Windows")
    win_path = os.path.join(win_root, "Fonts", cfg["win"])
    if os.path.exists(win_path):
        return win_path
        
    # 3. Check Linux truetype paths
    linux_base = "/usr/share/fonts/truetype"
    if os.path.exists(linux_base):
        # Try primary linux path
        lin_path = os.path.join(linux_base, cfg["linux"])
        if os.path.exists(lin_path):
            return lin_path
            
        # Try fallback linux path
        lin_fallback = os.path.join(linux_base, cfg["linux_fallback"])
        if os.path.exists(lin_fallback):
            return lin_fallback
            
        # Last resort: scan linux truetype dir for matching filename
        for root, dirs, files in os.walk(linux_base):
            for file in files:
                if file.lower() == cfg["win"].lower():
                    return os.path.join(root, file)

    return cfg["win"]  # Fallback to current working directory or path search

def generate_letter_image(
    char: str,
    font_name: str = "arial_black",
    font_size: int = 70,
    text_color: str | tuple | list = (255, 255, 255),
    outline_color: str | tuple | list = (0, 0, 0),
    outline_width: int = 6,
    bg_style: str = "transparent",  # "transparent", "circle", "square", "emoji_red"
    bg_color: str | tuple | list = (0, 0, 0, 0),
) -> bytes:
    """Draws a premium style letter on 100x100 transparent canvas"""
    img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Load font
    font_path = get_font_path(font_name)
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception as e:
        logger.warning(f"Failed to load font {font_path}, using default: {e}")
        font = ImageFont.load_default()

    # 2. Draw background shape
    if bg_style == "circle":
        draw.ellipse([4, 4, 96, 96], fill=bg_color)
    elif bg_style == "square":
        draw.rounded_rectangle([4, 4, 96, 96], radius=15, fill=bg_color)
    elif bg_style == "emoji_red":
        draw.rounded_rectangle([4, 4, 96, 96], radius=15, fill=(230, 50, 50, 255))
        text_color = (255, 255, 255, 255)

    # 3. Get text bounding box for centering
    try:
        bbox = draw.textbbox((0, 0), char, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (100 - text_w) // 2 - bbox[0]
        y = (100 - text_h) // 2 - bbox[1]
    except AttributeError:
        # Fallback for older PIL versions
        text_w, text_h = draw.textsize(char, font=font)
        x = (100 - text_w) // 2
        y = (100 - text_h) // 2

    # 4. Draw outline/stroke if configured
    if outline_width > 0:
        draw.text(
            (x, y),
            char,
            font=font,
            fill=outline_color,
            stroke_width=outline_width,
            stroke_fill=outline_color,
        )

    # 5. Draw text fill (with gradient support)
    is_gradient = (
        isinstance(text_color, list | tuple) 
        and len(text_color) == 2 
        and isinstance(text_color[0], list | tuple)
    )

    if is_gradient:
        # Create gradient image
        grad_img = Image.new("RGBA", (100, 100))
        grad_draw = ImageDraw.Draw(grad_img)
        c_start, c_end = text_color
        
        # Normalize transparency
        c_start = tuple(c_start) + (255,) if len(c_start) == 3 else tuple(c_start)
        c_end = tuple(c_end) + (255,) if len(c_end) == 3 else tuple(c_end)

        for y_pos in range(100):
            ratio = y_pos / 100.0
            r = int(c_start[0] + (c_end[0] - c_start[0]) * ratio)
            g = int(c_start[1] + (c_end[1] - c_start[1]) * ratio)
            b = int(c_start[2] + (c_end[2] - c_start[2]) * ratio)
            a = int(c_start[3] + (c_end[3] - c_start[3]) * ratio)
            grad_draw.line([(0, y_pos), (100, y_pos)], fill=(r, g, b, a))

        # Text mask
        mask = Image.new("L", (100, 100), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.text((x, y), char, font=font, fill=255)

        # Composite gradient onto letter
        img.paste(grad_img, (0, 0), mask=mask)
    else:
        draw.text(
            (x, y),
            char,
            font=font,
            fill=text_color,
        )

    out = io.BytesIO()
    img.save(out, format="WEBP", quality=95, lossy=True)
    return out.getvalue()

async def create_letter_pack(
    bot: Bot,
    user_id: int,
    name_short: str,
    title: str,
    lang: str = "uk",
    style_options: dict = None,
) -> str:
    """Generates all letters for selected alphabet and creates a custom emoji set in Telegram"""
    if style_options is None:
        style_options = {}

    alphabet = ALPHABETS.get(lang.lower(), ALPHABETS["uk"])
    me = await bot.get_me()
    full_name = f"{name_short}_by_{me.username}"
    full_title = f"{title} by @{me.username}"

    # emoji_list must contain real Unicode emoji that Telegram associates with each letter
    # when the user types in the message field.
    # Standard letters are not emojis, and regional indicator symbols are not accepted
    # as standalone emojis by Telegram. Thus, we map them to valid standard Unicode emojis,
    # prioritizing negative-squared and letter-like emojis (🅰️, 🅱️, 🆑, 🆔, etc.).
    LETTER_EMOJI_MAP = {
        # Latin — standard letters mapped to block/squared, symbol or country flag emojis
        "A": ["🅰️", "🇦🇺", "🔤"],
        "B": ["🅱️", "🇧🇪", "🔤"],
        "C": ["🇨🇦", "🆑", "🆒", "🔤"],
        "D": ["🇩🇰", "🆔", "🔤"],
        "E": ["🇪🇪", "🆓", "🆕", "🔤"],
        "F": ["🇫🇷", "🆓", "🔤"],
        "G": ["🇬🇧", "🆖", "🔤"],
        "H": ["🇭🇺", "🔤"],
        "I": ["ℹ️", "🇮🇹", "🔤"],
        "J": ["🇯🇵", "🔤"],
        "K": ["🇰🇪", "🆗", "🔤"],
        "L": ["🇱🇻", "🆑", "🆒", "🔤"],
        "M": ["Ⓜ️", "🇲🇽", "🔤"],
        "N": ["🇳🇴", "🆕", "🆖", "🔤"],
        "O": ["🅾️", "🇴🇲", "🔤"],
        "P": ["🅿️", "🇵🇱", "🔤"],
        "Q": ["🇶🇦", "🔤"],
        "R": ["®️", "🇷🇴", "🆓", "🔤"],
        "S": ["🆘", "🇸🇪", "🆚", "🔤"],
        "T": ["🇹🇷", "🔤"],
        "U": ["🇺🇦", "🆙", "🆒", "🔤"],
        "V": ["🆚", "🇻🇳", "🔤"],
        "W": ["🇼🇸", "🆕", "🔤"],
        "X": ["❎", "🇽🇰", "🔤"],
        "Y": ["🇾🇪", "🔤"],
        "Z": ["💤", "🇿🇼", "🔤"],
        # Cyrillic — mapped to corresponding block/squared, symbol or country flag emojis in Ukrainian
        "А": ["🅰️", "🇦🇹", "🔤"],
        "Б": ["🅱️", "🇧🇪", "🔤"],
        "В": ["🇬🇧", "🇻🇳", "🅱️", "🔤"],
        "Г": ["🇬🇷", "🆖", "🔤"],
        "Ґ": ["🇬🇪", "🆖", "🔤"],
        "Д": ["🇩🇰", "🆔", "🔤"],
        "Е": ["🇪🇪", "🔤"],
        "Є": ["🇪🇬", "🔤"],
        "Ж": ["🟡", "🟢", "🔤"],
        "З": ["🇿🇲", "💤", "🔤"],
        "И": ["ℹ️", "🔤"],
        "І": ["🇮🇹", "ℹ️", "🔤"],
        "Ї": ["🇮🇱", "ℹ️", "🔤"],
        "Й": ["🇾🇪", "ℹ️", "🔤"],
        "К": ["🇨🇦", "🆗", "🔤"],
        "Л": ["🇱🇻", "🆑", "🔤"],
        "М": ["Ⓜ️", "🇲🇽", "🔤"],
        "Н": ["🇳🇱", "🔤"],
        "О": ["🅾️", "🇴🇲", "🔤"],
        "П": ["🇵🇱", "🅿️", "🔤"],
        "Р": ["🇷🇴", "®️", "🔤"],
        "С": ["🇸🇪", "🆑", "🔤"],
        "Т": ["🇹🇷", "🔤"],
        "У": ["🇺🇦", "🆙", "🔤"],
        "Ф": ["🇫🇷", "🆓", "🔤"],
        "Х": ["🇭🇷", "❎", "🔤"],
        "Ц": ["🇨🇫", "🆑", "🔤"],
        "Ч": ["🇲🇪", "🆑", "🔤"],
        "Ш": ["🇨🇭", "🆘", "🔤"],
        "Щ": ["🇸🇪", "🆘", "🔤"],
        "Ь": ["🅱️", "🔤"],
        "Ю": ["🇿🇦", "🆙", "🔤"],
        "Я": ["🇯🇵", "®️", "🔤"],
    }
    FALLBACK_EMOJI = "🔤"

    stickers = []

    # Render all letters in alphabet
    for char in alphabet:
        sticker_data = generate_letter_image(char, **style_options)

        emojis = LETTER_EMOJI_MAP.get(char.upper(), LETTER_EMOJI_MAP.get(char, [FALLBACK_EMOJI]))

        input_sticker = InputSticker(
            sticker=BufferedInputFile(sticker_data, filename=f"letter_{char}.webp"),
            emoji_list=emojis,
            keywords=[char, char.lower(), f"letter {char.lower()}"],
            format="static",
        )
        stickers.append(input_sticker)

    # Call Telegram Bot API to create new custom emoji set
    await bot.create_new_sticker_set(
        user_id=user_id,
        name=full_name,
        title=full_title,
        stickers=stickers,
        sticker_type="custom_emoji",
    )
    
    return full_name
