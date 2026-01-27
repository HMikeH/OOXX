"""
chat_events.py - 聊天室事件處理
負責處理聊天消息的即時通訊
"""

from flask import session
from flask_socketio import emit
from datetime import datetime


def register_chat_events(socketio):
    """
    註冊聊天相關的 Socket.IO 事件
    
    Args:
        socketio: SocketIO 實例
    """
    
    @socketio.on('chat message')
    def handle_chat_message(msg):
        """
        處理聊天消息
        
        Args:
            msg: 聊天消息內容
        """
        if isinstance(msg, dict):
            message = msg.get('message', '')
            username = session.get('user') or msg.get('username') or '隱藏玩家'
            time_str = msg.get('time') or datetime.now().strftime('%H:%M:%S')
        else:
            message = str(msg)
            username = session.get('user', '隱藏玩家')
            time_str = datetime.now().strftime('%H:%M:%S')

        # 廣播給所有人
        emit('chat message', {
            'username': username,
            'message': message,
            'time': time_str
        }, broadcast=True)
