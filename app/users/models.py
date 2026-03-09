from sqlalchemy.orm import Mapped,mapped_column

from app.store.database.sqlalchemestry_base import BaseModel

class UserModel(BaseModel):
    __tablename__ = "users"
    username:Mapped[str]=mapped_column(nullable=False)
    id:Mapped[str]=mapped_column(primary_key=True,unique=True,nullable=False)
