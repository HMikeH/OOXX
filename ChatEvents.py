"""
chat_events.py - 聊天室事件處理
負責處理聊天消息的即時通訊
"""

from flask import session, request
from flask_socketio import emit
from datetime import datetime


# 存儲在線用戶 {sid: {'username': ..., 'sid': ...}}
online_users = {}


def register_chat_events(socketio):
    """
    註冊聊天相關的 Socket.IO 事件
    
    Args:
        socketio: SocketIO 實例
    """
    
    @socketio.on('connect')
    def handle_connect():
        """處理用戶連接，加入在線列表"""
        sid = request.sid
        username = session.get('user', '訪客')
        online_users[sid] = {
            'sid': sid,
            'username': username
        }
        # 廣播在線用戶列表
        emit('online_users', list(online_users.values()), broadcast=True)
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """處理用戶斷開，移出在線列表"""
        sid = request.sid
        if sid in online_users:
            del online_users[sid]
        # 廣播在線用戶列表
        emit('online_users', list(online_users.values()), broadcast=True)
    
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
    
    @socketio.on('private_message')
    def handle_private_message(data):
        """
        處理私聊消息
        
        Args:
            data: 包含 message, time, to(目標sid) 的字典
        """
        message = data.get('message', '')
        to_sid = data.get('to', '')
        username = session.get('user', '隱藏玩家')
        time_str = data.get('time') or datetime.now().strftime('%H:%M:%S')
        
        msg_data = {
            'username': username,
            'message': message,
            'time': time_str
        }
        
        # 發給目標用戶
        emit('private_message', msg_data, room=to_sid)
        
        # 也發給自己（顯示已發送）
        emit('private_message', msg_data)
