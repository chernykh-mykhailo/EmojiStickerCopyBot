from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from database.connection import DatabaseHelper

class UserRepository:
    def __init__(self, db_helper: DatabaseHelper):
        self.db_helper = db_helper

    async def get_by_tg_id(self, tg_id: int) -> User | None:
        async with self.db_helper.session() as session:
            stmt = select(User).where(User.telegram_id == tg_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def create_or_update(self, tg_id: int, username: str | None, full_name: str, language_code: str) -> User:
        async with self.db_helper.session() as session:
            stmt = select(User).where(User.telegram_id == tg_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                user.username = username
                user.full_name = full_name
                user.language_code = language_code
            else:
                user = User(
                    telegram_id=tg_id,
                    username=username,
                    full_name=full_name,
                    language_code=language_code
                )
                session.add(user)
            
            await session.flush()
            await session.refresh(user)
            return user
