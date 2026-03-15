from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.store.database.sqlalchemestry_base import BaseModel


class AdminModel(BaseModel):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    tg_user_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, unique=True
    )
