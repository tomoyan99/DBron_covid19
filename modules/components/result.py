def comp_result(is_show):
    if is_show:
        return """
        <div id="result_popup" class="hidden">
            <div id="popup-container">
                <p>送信完了しました！</p>
                <button id="complete-button" onclick="location.href='/mypage'">マイページに戻る</button>
            </div>
        </div>
        """
    else:
        return None
