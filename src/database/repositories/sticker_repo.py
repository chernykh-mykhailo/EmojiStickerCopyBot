from sqlalchemy import select
from database.models import StickerSet
from database.connection import DatabaseHelper


class StickerRepository:
    def __init__(self, db_helper: DatabaseHelper):
        self.db_helper = db_helper

    async def get_by_name(self, name: str) -> StickerSet | None:
        async with self.db_helper.session() as session:
            stmt = select(StickerSet).where(StickerSet.name == name)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def create(
        self,
        name: str,
        title: str,
        creator_id: int,
        set_type: str,
        sticker_count: int = 0,
    ) -> StickerSet:
        async with self.db_helper.session() as session:
            sticker_set = StickerSet(
                name=name,
                title=title,
                creator_id=creator_id,
                set_type=set_type,
                sticker_count=sticker_count,
            )
            session.add(sticker_set)
            await session.flush()
            await session.refresh(sticker_set)
            return sticker_set

    async def increment_count(self, name: str, amount: int = 1):
        async with self.db_helper.session() as session:
            stmt = select(StickerSet).where(StickerSet.name == name)
            result = await session.execute(stmt)
            sticker_set = result.scalar_one_or_none()
            if sticker_set:
                sticker_set.sticker_count += amount
                await session.commit()

    async def get_by_creator(self, creator_id: int) -> list[StickerSet]:
        async with self.db_helper.session() as session:
            stmt = (
                select(StickerSet)
                .where(StickerSet.creator_id == creator_id)
                .order_by(StickerSet.created_at.desc())
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())
