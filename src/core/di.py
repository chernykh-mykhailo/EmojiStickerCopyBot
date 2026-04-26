import punq
from aiogram import Bot
from database.connection import DatabaseHelper
from database.repositories.user_repo import UserRepository
from database.repositories.sticker_repo import StickerRepository
from services.user_service import UserService
from services.sticker_service import StickerService
from services.pack_service import PackService
from core.config import config
from core.bot_instance import bot

def setup_di() -> punq.Container:
    container = punq.Container()

    # Infrastructure
    container.register(DatabaseHelper, instance=DatabaseHelper(config.database_url))
    
    # Repositories
    container.register(UserRepository)
    container.register(StickerRepository)

    # Bot
    container.register(Bot, instance=bot)

    # Services
    container.register(UserService)
    container.register(StickerService)
    container.register(PackService)

    return container

container = setup_di()
