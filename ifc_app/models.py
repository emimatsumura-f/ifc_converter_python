from ifc_app.db import get_db

class User:
    def __init__(self, id, username):
        self.id = id
        self.username = username

    @staticmethod
    def get(id):
        db = get_db()
        user = db.execute(
            'SELECT * FROM user WHERE id = ?', (id,)
        ).fetchone()
        if not user:
            return None
        return User(user['id'], user['username'])

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)