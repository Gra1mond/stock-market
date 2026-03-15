import typing

from sqlalchemy import select

from app.base.base_accessor import BaseAccessor
from app.users.models import UserModel
from app.web.config import UserConfig

if typing.TYPE_CHECKING:
    from app.web.app import Application


class UserAccessor(BaseAccessor):
    async def connect_user(
        self, current_id: str, app: "Application", input_username: str
    ) -> UserConfig:
        new_user = UserConfig(
            user_id=current_id,
        )
        existing_user = await self.get_by_user_id(current_id)

        if existing_user:
            app.logger.info(
                "Пользователь %s уже существует, подключение ", current_id
            )
            user_config = new_user
        else:
            app.logger.info("Создаем нового пользователя %s", current_id)

            await self.create_user(id=current_id, username=input_username)
            """Добавить сюда username при регистрации и подключить его в view"""
            user_config = new_user
            app.config.users.append(new_user)

        return user_config

    async def get_by_user_id(self, current_id: str) -> UserModel | None:
        if not self.app.database.session:
            return None
        async with self.app.database.session() as session:
            return await session.scalar(
                select(UserModel).where(UserModel.id == current_id)
            )

    async def create_user(
        self, id: str, username: str, is_admin: bool = False
    ) -> UserModel:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        new_user = UserModel(username=username, id=id, is_admin=is_admin)
        async with self.app.database.session() as session:
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            return new_user
