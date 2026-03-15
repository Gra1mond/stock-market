import typing

from app.store.database.database import Database

if typing.TYPE_CHECKING:
    from app.web.app import Application


class Store:
    def __init__(self, app: "Application"):
        from app.game.accessor import GameAccessor
        from app.store.admin.accessor import AdminAccessor
        from app.store.bot.accessor import BotAccessor
        from app.store.users.accessor import UserAccessor

        self.user: UserAccessor = UserAccessor(app)
        self.game: GameAccessor = GameAccessor(app)
        self.bot: BotAccessor = BotAccessor(app)
        self.admins: AdminAccessor = AdminAccessor(app)


def setup_store(app: "Application"):
    app.database = Database(app)
    app.on_startup.append(app.database.connect)
    app.on_cleanup.append(app.database.disconnect)
    app.store = Store(app)
