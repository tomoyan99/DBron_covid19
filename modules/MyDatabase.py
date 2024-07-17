import mysql.connector as mydb
import sys
import pandas as pd
import re


class MyDatabase:
    def __init__(self, dsn):
        self.dsn = dsn
        self.dbcon, self.cur = self._connect()

    def _connect(self):
        try:
            dbcon = mydb.connect(**self.dsn)
            cur = dbcon.cursor(dictionary=True)
        except mydb.Error as e:
            print("DBコネクションでエラー発生", e)
            sys.exit()
        return dbcon, cur

    def _execute_query(self, sqlstring):
        try:
            self.cur.execute(sqlstring)
        except mydb.Error as e:
            print("クエリ実行でエラー発生", e)
            print("sqlstring =", sqlstring)
            sys.exit()

    def write(self, table_name, data):
        try:
            columns = ", ".join(data.keys())
            row_values = ", ".join(
                [f"'{str(value)}'" if isinstance(value, str) else str(value) for value in data.values()])
            sql = f"INSERT INTO {table_name} ({columns}) VALUES ({row_values})"
            self._execute_query(sql)
            self.dbcon.commit()

        except mydb.Error as e:
            print("書き込みエラー", e)
            sys.exit()

    def read(self, sql):
        try:
            self._execute_query(sql)
            result = self.cur.fetchall()
            # データの存在確認
            if len(result) == 0:
                field_names = [i[0] for i in self.cur.description]
                result = [{field: '' for field in field_names}]

            return pd.DataFrame(result)

        except mydb.Error as e:
            print("読み込みエラー", e)
            sys.exit()

    def exec_all_query(self,queries):
        try:
            for query in queries:
                self.cur.execute(query)

            self.dbcon.commit()
        except mydb.Error as e:
            print("書き込みエラー", e)
            sys.exit()

    def check_exist_primal(self, primal_key):
        try:
            sql = f"SELECT COUNT(*) FROM basic_information WHERE User_code = '{primal_key}'"
            self._execute_query(sql)
            result = self.cur.fetchall()
            # 一つもなかったらFalse,一つでもあったらTrue
            return not result[0]["COUNT(*)"] == 0
        except mydb.Error as e:
            print("読み込みエラー", e)
            sys.exit()

    def close(self):
        self.cur.close()
        self.dbcon.close()
