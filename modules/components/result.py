def comp_result(is_show,User_code):
    if is_show:
        return f"""
        <div id="result_popup" class="hidden">
            <div id="popup-container">
                <p>送信完了しました！</p>
                <button id="complete-button" onclick="location.href='/fetch:{User_code}'">マイページに戻る</button>
            </div>
        </div>
        """
    else:
        return None
