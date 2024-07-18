from datetime import datetime

from flask import Flask, render_template, session, request, redirect, abort
from flask_session import Session

import pandas as pd


# DBの1とか0とかを任意の文字に変えるやつ
def replace_df_values(df: pd.DataFrame, true_word='true_word', false_word='false_word', nan_word='nan_word'):
    # "0"をfalse_wordに置換
    df.replace(0, false_word, inplace=True)
    # "1"をtrue_wordに置換
    df.replace(1, true_word, inplace=True)
    # NaNをnan_wordに置換
    df.replace("nan", nan_word, inplace=True)
    # 空白をnan_wordに置換
    df.replace("", nan_word, inplace=True)
    return df

# 数字・文字列の1,0をT/Fに変える関数
def num_conv_tf(num):
    return True if (num == "1" or num == 1) else False

