import json
import secrets
import time

import numpy as np
import pandas as pd
from flask import Flask, render_template, session, request, redirect, abort

from modules.MyDatabase import MyDatabase
from flask_session import Session
from modules.components.logout import comp_logout
from modules.components.result import comp_result
from datetime import datetime
import math

# ランダムなSECRET_KEYを生成
secret_key = secrets.token_hex(32)

# データベース名
DB_name = "covid19"

app = Flask(__name__)
# セッションの設定
app.config['SECRET_KEY'] = secret_key
app.config['SESSION_TYPE'] = 'filesystem'

# セッションを初期化
Session(app)

# データベース変数の初期化
DB = None


# エラータイトルと詳細を、エラーページに表示する関数
def goto_error(title, desc):
    session.clear()
    session["error"] = json.dumps({"title": str(title), "desc": str(desc)})
    return redirect("/error")


# DBの1とか0とかを任意の文字に変えるやつ
def replace_df_values(df, true_word='true_word', false_word='false_word', nan_word='nan_word'):
    # "0"をfalse_wordに置換
    df.replace(0, false_word, inplace=True)
    # "1"をtrue_wordに置換
    df.replace(1, true_word, inplace=True)
    # NaNをnan_wordに置換
    df.replace("nan", nan_word, inplace=True)
    # 空白をnan_wordに置換
    df.replace("", nan_word, inplace=True)
    return df


# ユーザーデータ、健康管理表、行動管理表のデータをまとめた、
# main_dataを作る関数
def create_main_data(User_code):
    if DB.check_exist_primal(User_code):
        user_data_sql = f"""
                            select * from users 
                                where User_code = '{User_code}';
                            """
        health_data_sql = f"""
                            select * from health
                                where User_code = '{User_code}' 
                                AND Updated >= NOW() - INTERVAL 7 DAY
                                ORDER BY Updated DESC; 
                            """
        activity_data_sql = f"""
                            select * from activity
                                where User_code = '{User_code}' 
                                AND Updated >= NOW() - INTERVAL 7 DAY
                                ORDER BY Updated DESC;
                            """
        infection_data_sql = f"""
                            select * from infection
                                where User_code = '{User_code}'                                
                                AND Infection_stop >= NOW() - INTERVAL 1 YEAR
                                ORDER BY Infection_stop DESC;
                            """

        vaccine_data_sql = f"""
                            select * from vaccine
                                where User_code = '{User_code}'
                                AND vaccine_date >= NOW() - INTERVAL 1 YEAR
                                ORDER BY vaccine_date DESC;
                            """

        user_data = DB.read(user_data_sql)
        health_data = DB.read(health_data_sql)
        activity_data = DB.read(activity_data_sql)
        infection_data = DB.read(infection_data_sql)
        vaccine_data = DB.read(vaccine_data_sql)

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

        return user_data, health_data, activity_data, infection_data, vaccine_data
    else:
        raise Exception("データベースにユーザーが見つからない")


# request.formから現在時刻、User_codeを追加したdictを返す
def form_to_data(form,is_updated=True):
    form_dict = form.to_dict()
    # 現在時刻を取得
    now = datetime.now()
    # MySQLのTIMESTAMP形式にフォーマット
    updated = now.strftime('%Y-%m-%d %H:%M:%S')

    form_dict["User_code"] = session["user_data"]["User_code"][0]
    if is_updated:
        form_dict["Updated"] = updated

    return form_dict


# ルート画面。
# 今はテスト画面を表示してるけど、そのうちsigninにリダイレクトする予定
@app.route('/')
def home():
    session.clear()
    session["error"] = json.dumps({"title": "", "desc": ""})
    if DB:
        pass
    else:
        return goto_error("データベースエラー", "データベースに接続できませんでした")

    return redirect('/test')
    # return redirect('/login')


@app.route("/test")
def test():
    return render_template("test.html")


# ログイン画面
@app.route("/login", methods=["get", "post"])
def login():
    session.clear()
    if not request.form:
        return render_template("logins/login.html")
    else:
        User_code = request.form.get("User_code", default=None, type=str)
        if User_code:
            session["User_code"] = User_code
            # print(DB.check_exist_primal(User_code))
            if not DB.check_exist_primal(User_code):
                return goto_error("未登録エラー", "そのIDのユーザーは登録されていません")
        else:
            return goto_error("ID未入力エラー", "IDが入力されませんでした")
        return redirect(f"/fetch:{User_code}")


# サインアップ画面
@app.route("/signup", methods=["get", "post"])
def signup():
    session.clear()
    if not request.form:
        return render_template("logins/signup.html")
    else:
        # formの結果をミュータブルなdictに変換
        signup_data = request.form.to_dict()
        # 何らかの影響でformデータがなかったらエラー
        if not signup_data:
            return goto_error("サインアップエラー", "サインアップデータが取得できませんでした")
        if DB.check_exist_primal(signup_data["User_code"]):
            return goto_error("ユーザー登録済みエラー", "その学籍番号のユーザーはすでに登録されています")
        else:
            # 管理者パスワードをチェックして管理者権限の有無を付与
            signup_data["Admin_rights"] = "1" if signup_data["Admin_password"] == "admin" else "0"
            # signup_dataからAdmin_passwordプロパティの削除
            del signup_data["Admin_password"]
            User_code = signup_data["User_code"]
            # DBにユーザーを追加
            DB.write("users", signup_data)
            del signup_data
            return redirect(f"/fetch:{User_code}")


@app.route("/fetch:<User_code>")
def fetch_data(User_code):
    # ユーザごとの情報をだけを抽出
    (user_data,
     health_data,
     activity_data,
     infection_data,
     vaccine_data
     ) = create_main_data(User_code)
    session["user_data"] = user_data
    session["health_data"] = health_data.values
    session["activity_data"] = activity_data.values
    session["infection_data"] = infection_data.values
    session["vaccine_data"] = vaccine_data.values
    return redirect(f"/mypage:{User_code}")


# マイページ画面
@app.route("/mypage:<User_code>")
def mypage(User_code):
    try:
        referer = request.headers.get('Referer')
        # Refererが /login を含むかチェック
        if referer and ("/login" in referer or
                        "/signup" in referer or
                        f"/mypage:{User_code}" in referer
        ):

            is_completed_health = (not type(session["health_data"][0][-1]) == str
                                   and session["health_data"][0][-1].date() == datetime.now().date())
            is_completed_activity = (not type(session["activity_data"][0][-1]) == str
                                     and session["activity_data"][0][-1].date() == datetime.now().date())
            is_admin = True if session["user_data"]["Admin_rights"][0] == 1 else False
            if is_admin:
                return render_template("/mypages/admin_mypage.html",
                                       User_code=User_code,
                                       User_name=session["user_data"]["User_name"][0],
                                       Admin_rights=session["user_data"]["Admin_rights"][0],
                                       health_data=session["health_data"],
                                       activity_data=session["activity_data"],
                                       infection_data=session["infection_data"],
                                       vaccine_data=session["vaccine_data"],
                                       is_completed_health=is_completed_health,
                                       is_completed_activity=is_completed_activity
                                       )
            else:
                return render_template("/mypages/mypage.html",
                                       User_code=User_code,
                                       User_name=session["user_data"]["User_name"][0],
                                       Admin_rights=session["user_data"]["Admin_rights"][0],
                                       health_data=session["health_data"],
                                       activity_data=session["activity_data"],
                                       infection_data=session["infection_data"],
                                       vaccine_data=session["vaccine_data"],
                                       is_completed_health=is_completed_health,
                                       is_completed_activity=is_completed_activity
                                       )
        else:
            abort(403)  # Forbidden
    except Exception as e:
        print(e)
        return goto_error("マイページ読み込みエラー",
                          "マイページの読み込みに失敗しました。<br>セッション情報が初期化されたなどの原因が考えられます。<br>もう一度サインインからやり直してください")


# logout画面
@app.route("/mypage:<User_code>/logout")
def logout(User_code):
    is_completed_health = (not type(session["health_data"][0][-1]) == str
                           and session["health_data"][0][-1].date() == datetime.now().date())
    is_completed_activity = (not type(session["activity_data"][0][-1]) == str
                             and session["activity_data"][0][-1].date() == datetime.now().date())
    is_admin = True if session["user_data"]["Admin_rights"][0] == 1 else False
    if is_admin:
        return render_template("/mypages/admin_mypage.html",
                               User_code=User_code,
                               User_name=session["user_data"]["User_name"][0],
                               Admin_rights=session["user_data"]["Admin_rights"][0],
                               health_data=session["health_data"],
                               activity_data=session["activity_data"],
                               infection_data=session["infection_data"],
                               vaccine_data=session["vaccine_data"],
                               is_completed_health=is_completed_health,
                               is_completed_activity=is_completed_activity,
                               logout=comp_logout(True,User_code)
                               )
    else:
        return render_template("/mypages/mypage.html",
                               User_code=User_code,
                               User_name=session["user_data"]["User_name"][0],
                               Admin_rights=session["user_data"]["Admin_rights"][0],
                               health_data=session["health_data"],
                               activity_data=session["activity_data"],
                               infection_data=session["infection_data"],
                               vaccine_data=session["vaccine_data"],
                               is_completed_health=is_completed_health,
                               is_completed_activity=is_completed_activity,
                               logout=comp_logout(True,User_code)
                               )

# 健康記録画面
@app.route("/mypage:<User_code>/edit/health", methods=["GET", "POST"])
def edit_health(User_code):
    if not request.form:
        return render_template("mypages/subpages/health.html", result=comp_result(False, User_code))
    else:
        data = form_to_data(request.form)
        DB.write("health", data)
        return render_template("mypages/subpages/health.html", result=comp_result(True, User_code))


# 活動記録画面
@app.route("/mypage:<User_code>/edit/activity", methods=["GET", "POST"])
def edit_activity(User_code):
    if not request.form:
        return render_template("mypages/subpages/activity.html", result=comp_result(False, User_code))
    else:
        data = form_to_data(request.form)
        DB.write("activity", data)
        return render_template("mypages/subpages/activity.html", result=comp_result(True, User_code))


# 観戦記録画面
@app.route("/mypage:<User_code>/edit/infection", methods=["GET", "POST"])
def edit_infection(User_code):
    if not request.form:
        return render_template("mypages/subpages/infection.html", result=comp_result(False, User_code))
    else:
        data = form_to_data(request.form,False)
        DB.write("infection", data)
    return render_template("mypages/subpages/infection.html", result=comp_result(True, User_code))


# ワクチン接種記録画面
@app.route("/mypage:<User_code>/edit/vaccine", methods=["GET", "POST"])
def edit_vaccine(User_code):
    if not request.form:
        return render_template("mypages/subpages/vaccine.html", result=comp_result(False, User_code))
    else:
        data = form_to_data(request.form,False)
        DB.write("vaccine", data)
    return render_template("mypages/subpages/vaccine.html", result=comp_result(True, User_code))


# 編集更新
@app.route("/mypage:<User_code>/edit/update")
def edit_update(User_code):
    return render_template("mypages/subpages/update.html")


# 削除更新
# いる？
@app.route("/mypage:<User_code>/edit/delete")
def edit_delete(User_code):
    return render_template("mypages/subpages/delete.html")


# エラーページ画面
@app.route("/error")
def error():
    # エラー内容をまとめたobject
    error_obj = None
    if "error" in session:
        error_obj = json.loads(session.get('error'))
    else:
        error_obj = {"title": "不明なエラー", "desc": "不明なエラーが発生しました"}

    return render_template("error.html", title=error_obj["title"], desc=error_obj["desc"])


if __name__ == '__main__':
    dsn = {
        'host': 'localhost',  # ホスト名(IPアドレス)
        'port': '3306',  # mysqlの接続ポート番号
        'user': 'root',  # dbアクセスするためのユーザid
        'password': '1234',  # ユーザidに対応するパスワード
        'database': 'covid19'  # オープンするデータベース名
    }
    DB = MyDatabase(dsn)
    app.run(debug=True)
