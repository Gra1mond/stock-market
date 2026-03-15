import typing
from dataclasses import dataclass, field

import yaml

if typing.TYPE_CHECKING:
    from app.web.app import Application


@dataclass
class AdminConfig:
    email: str
    password: str
    tg_user_id: int


@dataclass
class BotConfig:
    token: str
    webhook_url: str


@dataclass
class UserConfig:
    user_id: str
    username: str | None = None


@dataclass
class SessionConfig:
    key: str


"""Добавить в датабазу данные пользователя"""


@dataclass
class DatabaseConfig:
    host: str
    port: int
    user: str
    password: str
    database: str


@dataclass
class Config:
    admin: AdminConfig
    bot: BotConfig
    database: DatabaseConfig
    session: SessionConfig
    users: list[UserConfig] = field(default_factory=list)


def setup_config(app: "Application", config_path: str):
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)

        session = SessionConfig(key=raw_config["session"]["key"])

        app.config = Config(
            bot=BotConfig(
                token=raw_config["bot"]["token"],
                webhook_url=raw_config["bot"]["webhook_url"],
            ),
            admin=AdminConfig(
                email=raw_config["admin"]["email"],
                password=raw_config["admin"]["password"],
                tg_user_id=raw_config["admin"]["tg_user_id"],
            ),
            database=DatabaseConfig(**raw_config["database"]),
            session=session,
        )
