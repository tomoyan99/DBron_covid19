import json
import secrets

from flask import Flask, render_template, session, request, redirect, abort

from modules.MyDatabase import MyDatabase
from flask_session import Session
from modules.components.result import comp_result

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


# ユーザーデータ、健康管理表、行動管理表のデータをまとめた、
# main_dataを作る関数
def create_main_data(User_code):
    if DB.check_exist_primal(User_code):
        user_data_sql = f"""
                            select * from basic_information 
                                where User_code = '{User_code}';
                            """
        health_data_sql = f"""
                            select * from health_observation
                                where User_code = '{User_code}' 
                                AND Updated >= NOW() - INTERVAL 7 DAY; 
                            """
        behavior_data_sql = f"""
                            select * from behavior_record
                                where User_code = '{User_code}' 
                                AND Updated >= NOW() - INTERVAL 7 DAY;
                            """
        infection_data_sql = f"""
                            select * from infection_status
                                where User_code = '{User_code}' 
                            """

        vaccine_data_sql = f"""
                            select * from vaccine
                                where User_code = '{User_code}' 
                            """

        user_data = DB.read(user_data_sql)
        health_data = DB.read(health_data_sql)
        behavior_data = DB.read(behavior_data_sql)
        infection_data = DB.read(infection_data_sql)
        vaccine_data = DB.read(vaccine_data_sql)

        del health_data["User_code"]
        del health_data["HealthID"]

        del behavior_data["User_code"]
        del behavior_data["BehaviorID"]
        del behavior_data["Is_companions"]

        del infection_data["User_code"]

        del vaccine_data["User_code"]
        del vaccine_data["vaccineID"]

        return user_data, health_data, behavior_data, infection_data, vaccine_data
    else:
        raise Exception("データベースにユーザーが見つからない")


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
    return render_template("test.html",result=comp_result(True))


# ログイン画面
@app.route("/login",methods=["get","post"])
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
@app.route("/signup",methods=["get","post"])
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
            DB.write("basic_information", signup_data)
            del signup_data
            return redirect(f"/fetch:{User_code}")


@app.route("/fetch:<User_code>")
def fetch_data(User_code):
    # ユーザごとの情報をだけを抽出
    (user_data,
     health_data,
     behavior_data,
     infection_data,
     vaccine_data
     ) = create_main_data(User_code)
    session["user_data"] = user_data
    session["health_data"] = health_data.values
    session["behavior_data"] = behavior_data.values
    session["infection_data"] = infection_data.values
    session["vaccine_data"] = vaccine_data.values
    return redirect("/mypage")


# マイページ画面
@app.route("/mypage")
def mypage():
    try:
        referer = request.headers.get('Referer')
        # Refererが /login を含むかチェック
        if referer and ("/login" in referer or "/signup" in referer or "/mypage" in referer):
            return render_template("/mypages/mypage.html",
                                   User_code=session["user_data"]["User_code"][0],
                                   User_name=session["user_data"]["User_name"][0],
                                   Admin_rights=session["user_data"]["Admin_rights"][0],
                                   health_data=session["health_data"],
                                   behavior_data=session["behavior_data"],
                                   infection_data=session["infection_data"],
                                   vaccine_data=session["vaccine_data"]
                                   )
        else:
            abort(403)  # Forbidden
    except Exception as e:
        print(e)
        return goto_error("マイページ読み込みエラー",
                          "マイページの読み込みに失敗しました。<br>セッション情報が初期化されたなどの原因が考えられます。<br>もう一度サインインからやり直してください")


# 健康記録画面
@app.route("/mypage/edit/health", methods=["GET","POST"])
def edit_health():
    if not request.form:
        return render_template("mypages/subpages/health.html", result=comp_result(False))
    else:
        print(json.dumps(request.form,indent=2))
        return render_template("mypages/subpages/health.html", result=comp_result(True))


# 活動記録画面
@app.route("/mypage/edit/behavior")
def edit_behavior():
    if not request.form:
        return render_template("mypages/subpages/behavior.html", result=comp_result(False))
    else:
        print(json.dumps(request.form,indent=2))
        return render_template("mypages/subpages/behavior.html", result=comp_result(True))


# 観戦記録画面
@app.route("/mypage/edit/infection")
def edit_infection():
    if not request.form:
        return render_template("mypages/subpages/infection.html", result=comp_result(False))
    else:
        print(json.dumps(request.form,indent=2))
    return render_template("mypages/subpages/infection.html", result=comp_result(True))


# ワクチン接種記録画面
@app.route("/mypage/edit/vaccine")
def edit_vaccine():
    if not request.form:
        return render_template("mypages/subpages/vaccine.html", result=comp_result(False))
    else:
        print(json.dumps(request.form,indent=2))
    return render_template("mypages/subpages/vaccine.html", result=comp_result(True))


# 編集更新
@app.route("/mypage/edit/update")
def edit_update():
    return render_template("mypages/subpages/update.html")


# 削除更新
# いる？
@app.route("/mypage/edit/delete")
def edit_delete():
    return render_template("mypages/subpages/delete.html")


@app.route("/mypage/edit/result:<page_name>")
def edit_result(page_name):
    form_data = request.form
    print(json.dumps(form_data, indent=2))
    return render_template(f"mypages/subpages/{page_name}.html")


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
