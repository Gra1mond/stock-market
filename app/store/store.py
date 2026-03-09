import typing
from app.store.database.database import Database

if typing.TYPE_CHECKING:
    from app.web.app import Application
    from app.store.users.accessor import UserAccessor  

class Store:
    def __init__(self, app: "Application"):
        from app.store.users.accessor import UserAccessor
        
        
        self.user: UserAccessor = UserAccessor(self)

def setup_store(app: "Application"):
    app.database = Database
    app.on_startup.append(app.database.connect)
    app.on_cleanup.append(app.database.disconnect)  
    app.store = Store(app)