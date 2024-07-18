from datetime import datetime

from MyDatabase import MyDatabase
from modules.utils import replace_df_values


class User:
    def __init__(self, User_code:str, DB:MyDatabase):
        self.vaccine_data = None
        self.infection_data = None
        self.health_data = None
        self.user_data = None
        self.activity_data = None
        self.User_code = User_code
        self.DB = DB
        if self.DB.check_exist_primal(self.User_code):
            self.fetch_data()
        else:

    def fetch_data(self):
        # DBからデータを取得するロジックを実装
        user_data_sql = f"""
                                select * from users 
                                    where User_code = '{self.User_code}';
                                """
        health_data_sql = f"""
                                select * from health
                                    where User_code = '{self.User_code}' 
                                    AND Updated >= NOW() - INTERVAL 7 DAY
                                    ORDER BY Updated DESC; 
                                """
        activity_data_sql = f"""
                                select * from activity
                                    where User_code = '{self.User_code}' 
                                    AND Updated >= NOW() - INTERVAL 7 DAY
                                    ORDER BY Updated DESC;
                                """
        infection_data_sql = f"""
                                select * from infection
                                    where User_code = '{self.User_code}'                                
                                    AND Infection_stop >= NOW() - INTERVAL 1 YEAR
                                    ORDER BY Infection_stop DESC;
                                """

        vaccine_data_sql = f"""
                                select * from vaccine
                                    where User_code = '{self.User_code}'
                                    AND vaccine_date >= NOW() - INTERVAL 1 YEAR
                                    ORDER BY vaccine_date DESC;
                                """

        user_data = self.DB.read(user_data_sql)
        health_data = self.DB.read(health_data_sql)
        activity_data = self.DB.read(activity_data_sql)
        infection_data = self.DB.read(infection_data_sql)
        vaccine_data = self.DB.read(vaccine_data_sql)

        del health_data["User_code"]
        del health_data["Health_ID"]

        health_data = replace_df_values(health_data, "あり", "なし", "未記入")

        del activity_data["User_code"]
        del activity_data["Activity_ID"]
        del activity_data["Is_companions"]

        activity_data = replace_df_values(activity_data, "あり", "なし", "未記入")

        del infection_data["User_code"]

        infection_data = replace_df_values(infection_data, "はい", "いいえ", "未記入")

        del vaccine_data["User_code"]
        del vaccine_data["vaccine_ID"]

        vaccine_data = replace_df_values(vaccine_data, "", "", "未記入")

        self.user_data = user_data
        self.health_data = health_data
        self.activity_data = activity_data
        self.infection_data = infection_data
        self.vaccine_data = vaccine_data

    # request.formから現在時刻、User_codeを追加したdictを返す
    def form_to_data(self,form,is_updated=True):
        form_dict = form.to_dict()
        # 現在時刻を取得
        now = datetime.now()
        # MySQLのTIMESTAMP形式にフォーマット
        updated = now.strftime('%Y-%m-%d %H:%M:%S')

        form_dict["User_code"] = self.User_code
        if is_updated:
            form_dict["Updated"] = updated

        return form_dict

    def write_db(self,):
        data = form_to_data(request.form, False)
        DB.write("infection", data)
