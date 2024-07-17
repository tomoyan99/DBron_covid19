from modules.MyDatabase import MyDatabase
import pandas as pd
import datetime

# Data Source Nameのパラメータを辞書型変数で定義しオープン
dsn = {
    'host': 'localhost',  # ホスト名(IPアドレス)
    'port': '3306',  # mysqlの接続ポート番号
    'user': 'root',  # dbアクセスするためのユーザid
    'password': '1234',  # ユーザidに対応するパスワード
    'database': 'covid19'  # オープンするデータベース名
}

# 2つのファイル名をlist変数として保存
filename = [
    "./test_data/users.csv",
    "./test_data/health.csv",
    "./test_data/activity.csv",
    "./test_data/infection.csv",
    "./test_data/vaccine.csv"
]

# 現在の日時を取得
dt_now = datetime.datetime.now()


def create_test_data():
    db = MyDatabase(dsn)
    # 2つのファイルを処理するための繰り返し処理 fnにファイル名が入る
    for fn in filename:
        query_stacks = []
        # ファイルオープン 先頭行をheaderとして
        df = pd.read_csv(fn, header=0)
        print(fn)

        # recsetは，DataFrameのため，indexとrowdataをペアで取得する
        for ind, rowdata in df.iterrows():

            # レコードを挿入するSQL文をそれぞれ定義する
            if fn == "./test_data/users.csv":
                # basic_informationテーブルの場合
                query_stacks += [f"""
                    INSERT INTO users
                    (User_code,Faculty_office,User_name,Phone_number,Admin_rights)
                    values
                    ('{rowdata.User_code}','{rowdata.Faculty_office}','{rowdata.User_name}','{rowdata.Phone_number}',{rowdata.Admin_rights})
                    ;
                """]
            elif fn == "./test_data/health.csv":
                # healthテーブルの場合
                query_stacks += [f"""
                    INSERT INTO health
                    (User_code,Temperature,kinniku_pain,Darusa,Atama_ita,Nodo_ita,Iki_gire,Seki_kusyami,Hakike,Haraita,Mikaku,Kyukaku,Updated)
                    values
                    ('{rowdata.User_code}',{rowdata.Temperature},{rowdata.Kinniku_pain},{rowdata.Darusa},{rowdata.Atama_ita},{rowdata.Nodo_ita},{rowdata.Iki_gire},{rowdata.Seki_kusyami},{rowdata.Hakike},{rowdata.Haraita},{rowdata.Mikaku},{rowdata.Kyukaku},'{dt_now}')
                    ;
                """]
            elif fn == "./test_data/activity.csv":
                # activity_record.csvテーブルの場合
                query_stacks += [f"""
                    INSERT INTO activity
                    (User_code,Action_starttime,Action_endtime,Action_location,Move_method,Departure,Arrival,Is_companions,Companions,Special_notices,Updated)
                    values
                    ('{rowdata.User_code}','{rowdata.Action_starttime}','{rowdata.Action_endtime}','{rowdata.Action_location}','{rowdata.Move_method}','{rowdata.Departure}','{rowdata.Arrival}',{rowdata.Is_companions},'{rowdata.Companions}','{rowdata.Special_notices}','{dt_now}')
                    ;
                """]
            elif fn == "./test_data/infection.csv":
                # infectionテーブルの場合
                query_stacks += [f"""
                    INSERT INTO infection
                    (User_code,Infection_start,Infection_stop,Infection_status,medical_name,doctor_name)
                    values
                    ('{rowdata.User_code}','{rowdata.Infection_start}','{rowdata.Infection_stop}',{rowdata.Infection_status},'{rowdata.medical_name}','{rowdata.doctor_name}')
                    ;
                """]
            elif fn == "./test_data/vaccine.csv":
                # vaccineテーブルの場合
                query_stacks += [f"""
                    INSERT INTO vaccine
                    (User_code,vaccine_date,vaccine_name)
                    values
                    ('{rowdata.User_code}','{rowdata.vaccine_date}','{rowdata.vaccine_name}')
                    ;
                """]
        # クエリー実行
        db.exec_all_query(query_stacks)

        # INSERT文を実行するループが終了し，結果をフィードバック
        print(f"{fn}を{len(df)}レコードを新規挿入しました")

    # カーソルとDBコンソールのクローズ
    db.close()


create_test_data()
