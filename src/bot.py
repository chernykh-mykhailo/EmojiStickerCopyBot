import asyncio
import logging
import os
import sys

# Add current directory to path so imports work from src
sys.path.insert(0, os.path.dirname(__file__))
from core.bot_instance import bot, dp
from core.logger import setup_logger
from core.di import container
from database.connection import DatabaseHelper
from database.models import Base
from handlers import common, packs

async def main():
    setup_logger()
    logger = logging.getLogger(__name__)
    
    # Initialize database
    db_helper = container.resolve(DatabaseHelper)
    async with db_helper.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Register routers
    dp.include_router(common.router)
    dp.include_router(packs.router)
    
    logger.info("Bot started!")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
