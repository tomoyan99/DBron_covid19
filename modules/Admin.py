from modules.User import User


class Admin(User):
    def __init__(self, user_code, db):
        super().__init__(user_code, db)

    def fetch_all_users(self):
        # DBから全ユーザーのデータを取得するロジックを実装
        all_users = self.db.get_all_users()
        return all_users
