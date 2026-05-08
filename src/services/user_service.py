from database.repositories.user_repo import UserRepository
from database.models import User


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def get_or_create_user(
        self, tg_id: int, username: str | None, full_name: str, language_code: str
    ) -> User:
        return await self.user_repo.create_or_update(
            tg_id=tg_id,
            username=username,
            full_name=full_name,
            language_code=language_code,
        )
