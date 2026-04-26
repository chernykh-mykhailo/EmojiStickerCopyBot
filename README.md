# 🎭 EmojiStickerCopyBot

A sophisticated Telegram bot built with **Aiogram 3** designed to seamlessly copy emojis and stickers into custom packs. 

## ✨ Features

- **🚀 High Performance**: Built on top of `asyncio` and `aiogram 3`.
- **📦 Pack Management**: Easily create and manage your own sticker/emoji sets.
- **🌍 Localization**: Multi-language support (default: Ukrainian).
- **💾 Persistent Storage**: Uses SQLAlchemy with SQLite for robust data management.
- **🛠 Modular Architecture**: Clean and maintainable codebase with dependency injection (`punq`).

## 🛠 Tech Stack

- **Framework**: [Aiogram 3.x](https://docs.aiogram.dev/)
- **Database**: [SQLAlchemy](https://www.sqlalchemy.org/) + [Aiosqlite](https://github.com/omnilib/aiosqlite)
- **Settings**: [Pydantic Settings](https://docs.pydantic.dev/latest/usage/pydantic_settings/)
- **DI Container**: [Punq](https://github.com/bob-the-constructor/punq)
- **Image Processing**: [Pillow](https://python-pillow.org/)

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/EmojiStickerCopyBot.git
cd EmojiStickerCopyBot
```

### 2. Set up environment variables
Copy `.env.template` to `.env` and fill in your details:
```bash
cp .env.template .env
```
Edit `.env`:
```env
BOT_TOKEN=your_telegram_bot_token_here
DATABASE_URL=sqlite+aiosqlite:///bot.db
LOG_LEVEL=INFO
DEFAULT_LOCALE=uk
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the bot
```bash
python bot.py
```

## 📁 Project Structure

- `core/`: Core bot initialization and DI setup.
- `database/`: Models and database connection helpers.
- `handlers/`: Telegram update handlers (commands, messages).
- `keyboards/`: Inline and reply keyboard builders.
- `locales/`: Localization files.
- `services/`: Business logic and external API integrations.
- `utils/`: Common utilities and constants.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
