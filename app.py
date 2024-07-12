from flask import Flask, render_template, session, request, redirect, abort
from flask_session import Session
import secrets
from MyDatabase import MyDatabase
import json

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


# 管理者権限の有無、健康管理表、行動管理表のデータをまとめた、
# main_dataを作る関数
def create_main_data(User_code):
    if DB.check_exist_primal(User_code):
        user_infos = {}
        user_infos_sql = f"""
                            select * from basic_information 
                                where User_code = '{User_code}';
                            """
        health_observation_sql = f"""
                            select * from health_observation
                                where User_code = '{User_code}' 
                                AND Updated >= NOW() - INTERVAL 7 DAY; 
                            """
        behavior_record_sql = f"""
                            select * from behavior_record
                                where User_code = '{User_code}' 
                                AND Updated >= NOW() - INTERVAL 7 DAY;
                            """
        user_infos["user_recode"] = DB.read(user_infos_sql)
        user_infos["health_recode"] = DB.read(health_observation_sql)
        user_infos["behavior_record"] = DB.read(behavior_record_sql)
        return user_infos
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

    if 'visit_count' in session:
        session['visit_count'] = session.get('visit_count') + 1
    else:
        session['visit_count'] = 1
    return render_template('test.html', count=session["visit_count"])


# ログイン画面
@app.route("/login")
def login():
    session.clear()
    return render_template("logins/signin.html")


# サインアップ画面
@app.route("/signup")
def signup():
    return render_template("logins/signup.html")


# サインイン/データ処理部
@app.route("/data/login", methods=["post"])
def data_login():
    User_code = request.form.get("User_code", default=None, type=str)
    if User_code:
        session["User_code"] = User_code
        # print(DB.check_exist_primal(User_code))
        if not DB.check_exist_primal(User_code):
            return goto_error("未登録エラー", "そのIDのユーザーは登録されていません")
    else:
        return goto_error("ID未入力エラー", "IDが入力されませんでした")
    return redirect("/mypage")


# サインアップ/データ処理部
@app.route("/data/signup", methods=["post"])
def data_signup():
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
        session["User_code"] = signup_data["User_code"]
        # print(signup_data)
        # DBにユーザーを追加
        DB.write("basic_information", signup_data)
        return redirect("/mypage")


# マイページ画面
@app.route("/mypage")
def mypage():
    try:
        referer = request.headers.get('Referer')
        # Refererが /login を含むかチェック
        if referer and ("/login" in referer or "/signup" in referer):
            # 必要なユーザー情報だけを抽出
            main_data = create_main_data(session["User_code"])
            session["main_data"] = main_data
            return render_template("mypages/mypage.html")
        else:
            abort(403)  # Forbidden

    except Exception as e:
        return goto_error("マイページ読み込みエラー",
                          "マイページの読み込みに失敗しました。<br>セッション情報が初期化されたなどの原因が考えられます。<br>もう一度サインインからやり直してください")


@app.route("/mypage/health")
def health():
    return render_template("mypages/subpages/health.html")


@app.route("/mypage/begavior")
def action():
    return render_template("mypages/subpages/behavior.html")


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
