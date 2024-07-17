def comp_logout(is_show,User_code):
    if is_show:
        return f"""
        <div id="logout_popup">
            <div id="popup-container">
                <p>ログアウトしますか</p>
                <button id="complete-button" onclick="location.href='/login'">ログアウトする</button>
                <button id="complete-button" onclick="location.href='/mypage:{User_code}'">マイページに戻る</button>
            </div>
        </div>
        """
    else:
        return None
