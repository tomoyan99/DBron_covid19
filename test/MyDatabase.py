#データベース操作のためのライブラリ
import mysql.connector as mydb
import sys
import pandas as pd

def my_query(sqlstring , cur):#MYSQLにquery実行
    try:
        #クエリを実行する
        cur.execute( sqlstring )
    except mydb.Error as e:
        #クエリー実行にエラーが発生した場合，エラーメッセージとSQL文を表示しプログラム終了
        print("クエリ実行でエラー発生", e)
        print("sqlstring =",sqlstring)
        sys.exit()

def my_open( **dsn ):
#DBコネクションのインスタンス化
    try:
        #コネクションのインスタンス化
        dbcon = mydb.connect( **dsn )
        # DBを操作するためのカーソルの作成 dictionary=Trueは検索結果にフィールド名を含める場合
        cur = dbcon.cursor(dictionary=True)
    except mydb.Error as e:
        #コネクション時にエラーが発生した場合，プログラム終了
        print("DBコネクションでエラー発生", e)
        sys.exit()

    return dbcon , cur

def my_close(dbcon , cur ):
    cur.close()
    dbcon.close()
