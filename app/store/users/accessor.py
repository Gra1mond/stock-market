from app.base.base_accessor import BaseAccessor
import typing
from sqlalchemy import select

from app.users.models import UserModel
from app.web.config import UserConfig
if typing.TYPE_CHECKING:
    from app.web.app import Application

class UserAccessor(BaseAccessor):
    async def connect_user(self, current_id: str, app: "Application") -> UserConfig:
        new_user = UserConfig(user_id=current_id,)
        existing_user = await self.get_by_user_id(current_id)

        if existing_user:
            app.logger.info(f"Пользователь {current_id} уже существует, подключение ")
            user_config = new_user  
        else:
            app.logger.info(f"Создаем нового пользователя {current_id}")

            await self.create_user(id=current_id)
            """Добавить сюда username при регистрации и подключить его в view"""  
            user_config = new_user
            app.config.users.append(new_user)
        
        return user_config



    async def get_by_user_id(self,current_id:str)->UserModel | None:
        if not self.app.database.session:
            return None
        async with self.app.database.session() as session:
            result = await session.scalar(select(UserModel).where(UserModel.id==current_id))
            return result
        

    async def create_user(self,id:str,username:str)->UserModel:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        new_user = UserModel(username=username,id=id)
        async with self.app.database.session() as session:
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            return new_user