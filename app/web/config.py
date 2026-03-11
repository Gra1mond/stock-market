from dataclasses import dataclass, field
from typing import List

@dataclass
class BotConfig:
    token:str
    group_id:str

@dataclass
class UserConfig:
    user_id:str
    username:str|None = None

@dataclass
class SessionConfig:
    key:str
"""Добавить в датабазу данные пользователя"""
@dataclass
class DatabaseConfig:
    host:str
    port:int
    user:str
    password:str
    database:str

@dataclass
class Config:
    session:SessionConfig
    bot:BotConfig
    database:DatabaseConfig
    users:List[UserConfig] = field(default_factory=list)