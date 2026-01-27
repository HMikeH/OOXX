"""
WebApp.py - Flask 應用主程式（類別化）
負責路由管理和 HTTP 請求處理
"""

from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO
from flask_cors import CORS
import random

from Config import Config
from ChatEvents import register_chat_events
from GameEvents import register_game_events


class WebApp:
    """
    Web 應用類別
    管理 Flask 應用、Socket.IO 和所有路由
    """
    
    def __init__(self):
        """初始化 Web 應用"""
        # 創建 Flask 應用
        self.App = Flask(__name__)
        CORS(self.App)
        self.App.secret_key = Config.SECRET_KEY
        
        # 創建 Socket.IO 實例
        self.SocketIO = SocketIO(
            self.App, 
            async_mode='threading', 
            cors_allowed_origins="*"
        )
        
        # 註冊路由
        self.App.route('/login', methods=['GET', 'POST'])(self.login)
        self.App.route('/', methods=['GET', 'POST'])(self.home)
        self.App.route('/reset')(self.reset)
        self.App.route('/logout')(self.logout)
        
        # 註冊 Socket.IO 事件
        register_chat_events(self.SocketIO)
        register_game_events(self.SocketIO)
    
    # ============================================================
    # 路由處理函式
    # ============================================================
    
    def login(self):
        """
        登入頁面處理
        - GET: 顯示登入表單（隨機顯示 5 個圖示）
        - POST: 驗證登入資訊並創建 session
        """
        # 如果已登入，直接重定向到首頁
        if 'user' in session:
            return redirect(url_for('home'))
        
        error = None
        ICON_POOL = [
            '😺', '🐶', '🐼', '🚀', '🎃', 
            '🐧', '🐵', '🐸', '🦊', '🐢', 
            '🐟', '🐯', '🦁', '🐷', '🦄'
        ]
        
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            icon = request.form.get('icon')
            
            # 驗證輸入
            if not username:
                error = '請輸入使用者名稱'
            elif len(username) > 10:
                error = '使用者名稱不可超過 10 個字元'
            elif not icon:
                error = '請選擇一個圖示'
            elif icon not in ICON_POOL:
                # 檢查圖示是否在合法池中（避免惡意提交）
                error = '所選圖示無效，請重新選擇'
            else:
                # 登入成功
                session['user'] = username
                session['icon'] = icon
                return redirect(url_for('home'))
            
            # 驗證失敗，重新生成隨機圖示
            icons = random.sample(ICON_POOL, 5)
        else:
            # GET 請求：生成隨機圖示
            icons = random.sample(ICON_POOL, 5)
        
        return render_template('login.html', error=error, icons=icons)
    
    def home(self):
        """
        首頁處理
        顯示 PVP 遊戲界面
        """
        if 'user' not in session:
            return redirect(url_for('login'))
        
        return render_template(
            'index.html',
            username=session.get('user', '玩家')
        )
    
    def reset(self):
        """重定向到遊戲頁面"""
        return redirect(url_for('home'))
    
    def logout(self):
        """清除 session 並重定向到登入頁面"""
        session.clear()
        return redirect(url_for('login'))
    
    # ============================================================
    # 應用運行
    # ============================================================
    
    def run(self):
        """啟動 Web 應用"""
        self.SocketIO.run(
            self.App, 
            host=Config.HOST, 
            port=Config.FLASK_RUN_PORT, 
            debug=Config.DEBUG
        )


def StartWebApp():
    """啟動 Web 應用（主線程模式）"""
    webapp = WebApp()
    webapp.run()


if __name__ == '__main__':  # pragma: no cover
    StartWebApp()
