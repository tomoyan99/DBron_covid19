from modules.User import User


class Admin(User):
    def __init__(self, user_code, DB,data):
        super().__init__(user_code, DB,data)

    def fetch_all_users(self):
        
        # DBから全ユーザーのデータを取得するロジックを実装
        all_users = self.DB.read()
        return all_users
