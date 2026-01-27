"""
GameEvents.py - 遊戲事件處理
負責處理 PVP 對戰的遊戲邏輯和房間管理

事件流程
1. join_pvp - 玩家加入配對
2. make_move - 玩家下棋（使用座標）
3. move_made - 廣播棋盤更新
4. round_end - 遊戲回合結束
5. game_reset - 開始新回合
"""

from flask import session, request
from flask_socketio import emit, join_room, leave_room
from RoomManager import RoomManager
from datetime import datetime

# 創建房間管理器實例（Singleton 模式）
# 全域只有一個 RoomManager 實例，管理所有房間
room_manager = RoomManager()


def register_game_events(socketio):
    """
    註冊遊戲相關的 Socket.IO 事件監聽
    
    Args:
        socketio: SocketIO 實例
    """
    
    @socketio.on('join_pvp')
    def handle_join_pvp():
        """
        處理玩家加入 PVP 配對
        
        配對邏輯：
        1. 如果有等待中的房間 → 加入房間，遊戲開始
        2. 如果沒有等待中的房間：
           - 若已有遊戲進行中 → 拒絕加入（避免同時多場遊戲）
           - 若沒有遊戲進行中 → 創建新房間，等待對手加入
        """
        username = session.get('user', '匿名')
        sid = request.sid
        
        # 檢查是否有正在進行的遊戲（沒有等待中的房間）
        available_room = room_manager.get_available_room()
        active_game_count = room_manager.get_active_game_count()
        
        # 如果沒有等待中的房間，且已經有正在進行的遊戲，拒絕加入
        if not available_room and active_game_count > 0:
            emit('game_in_progress', {'message': '目前已有遊戲進行中，請稍後再試'})
            return
        
        # 嘗試尋找可用房間
        room_id = available_room
        
        if room_id:
            # 檢查房間是否已滿
            room = room_manager.get_room(room_id)
            if room and len(room.players) >= 2:
                emit('room_full', {'message': '房間已滿，請稍後再試'})
                return
            
            # 加入現有房間
            success = room_manager.join_room(room_id, sid, username)
            if success:
                join_room(room_id)
                room = room_manager.get_room(room_id)
                room_state = room.get_state()
                
                # 取得第一個玩家的名稱
                first_player_name = room_state['players'][0]['username']
                
                # 發送系統訊息到聊天室
                timestamp = datetime.now().strftime('%H:%M:%S')
                emit('chat message', {
                    'username': '系統',
                    'message': f'強勁的棋手 {first_player_name} 已等候多時!',
                    'time': timestamp
                }, room=room_id)
                timestamp = datetime.now().strftime('%H:%M:%S')
                emit('chat message', {
                    'username': '系統',
                    'message': f'強勁的棋手 {username} 已抵達戰場!',
                    'time': timestamp
                }, room=room_id)
                
                # 使用隨機分配的座位和符號
                left_player = room_state['left_player']
                right_player = room_state['right_player']
                
                # 左玩家先手
                first_turn = left_player['symbol']
                room.game.turn = first_turn
                
                for player in room.players:
                    my_side = 'left' if player.sid == left_player['sid'] else 'right'
                    emit('game_start', {
                        'room_id': room_id,
                        'your_symbol': player.symbol,
                        'turn': first_turn,
                        'left_player': left_player,
                        'right_player': right_player,
                        'my_side': my_side,
                        'scores': room_state['scores'],
                        'round_count': room_state['round_count']
                    }, room=player.sid)
            else:
                emit('room_full', {'message': '房間已滿，請稍後再試'})
        else:
            # 創建新房間（只有在沒有正在進行的遊戲時）
            room_id = room_manager.create_room(sid, username)
            join_room(room_id)
            # 回傳等待狀態
            emit('waiting_for_opponent', {'room_id': room_id, 'status': 'waiting'})
            timestamp = datetime.now().strftime('%H:%M:%S')
            emit('chat message', {
                'username': '系統',
                'message': '請等候其他玩家加入！',
                'time': timestamp
            }, room=room_id)

    @socketio.on('action')
    def handle_action(payload):
        """
        統一處理前端發來的 action 事件，根據 action 名稱轉發到對應函式
        """

        if not payload:
            return

        action_name = None
        if isinstance(payload, dict):
            action_name = payload.get('action')
        elif isinstance(payload, str):
            action_name = payload

        if action_name == 'join_pvp':
            # 直接呼叫既有的 handler
            return handle_join_pvp()

        if action_name == 'make_move':
            # 只接受統一格式：
            # { action: 'make_move', data: { row: <r>, col: <c> } }
            if isinstance(payload, dict):
                data = payload.get('data')
                # 若 data 為 None 或不包含 row/col，則不處理
                if data and isinstance(data, dict) and data.get('row') is not None and data.get('col') is not None:
                    return handle_make_move(data)
            # 否則忽略
            return

        if action_name == 'reset_game':
            # 透過 action 路徑觸發重置回合
            return handle_reset_game()

        if action_name == 'start_new_match':
            # 透過 action 路徑開始新比賽
            return handle_start_new_match()

    @socketio.on('make_move')
    def handle_make_move(data):
        """
        處理玩家移動（使用座標方式）
        
        Args:
            data: 包含移動資訊的字典 {'row': 行座標, 'col': 列座標}
        """
        sid = request.sid
        row = data.get('row')
        col = data.get('col')
        
        # 驗證座標
        if row is None or col is None or not (0 <= row <= 2) or not (0 <= col <= 2):
            return
        
        # 獲取玩家所在房間
        room_id = room_manager.get_room_by_sid(sid)
        if not room_id:
            return
        
        # 執行移動
        room_state = room_manager.make_move(room_id, sid, row, col)
        if room_state:
            # 只廣播必要的更新資訊（使用二維數組座標）
            emit('move_made', {
                'row': row,
                'col': col,
                'symbol': room_state['board'][row][col],
                'turn': room_state['turn']
            }, room=room_id)
            
            # 如果遊戲結束，發送結束資訊
            if room_state['winner']:
                winning_lines = get_winning_lines(room_state['board'])
                emit('round_end', {
                    'winner': room_state['winner'],
                    'scores': room_state['scores'],
                    'round_count': room_state['round_count'],
                    'match_finished': room_state['match_finished'],
                    'winning_lines': winning_lines
                }, room=room_id)

    @socketio.on('reset_game')
    def handle_reset_game():
        """
        處理遊戲重置請求（下一回合）
        """
        sid = request.sid
        room_id = room_manager.get_room_by_sid(sid)
        
        if room_id:
            room = room_manager.get_room(room_id)
            if room:
                room.reset()
                room_state = room.get_state()
                
                emit('game_reset', {
                    'turn': room_state['turn'],
                    'scores': room_state['scores'],
                    'round_count': room_state['round_count'],
                    'match_finished': room_state['match_finished'],
                    'current_first_player': room_state['current_first_player']
                }, room=room_id)

    @socketio.on('start_new_match')
    def handle_start_new_match():
        """
        處理開始新比賽請求（新的5戰3勝）
        """
        sid = request.sid
        room_id = room_manager.get_room_by_sid(sid)
        
        if room_id:
            room = room_manager.get_room(room_id)
            if room:
                # 重置所有分數和回合數
                room.scores = {'left': 0, 'right': 0, 'draw': 0}
                room.round_count = 0
                room.match_finished = False
                
                # 重新隨機分配座位和符號
                room._assign_seats_and_symbols()
                
                # 重置遊戲
                room.game.reset()
                room.game.turn = room.left_player.symbol
                room.game.started = True
                room.current_first_player = 'left'
                
                room_state = room.get_state()
                
                # 發送新比賽開始資訊
                emit('new_match_started', {
                    'turn': room_state['turn'],
                    'scores': room_state['scores'],
                    'round_count': room_state['round_count'],
                    'match_finished': room_state['match_finished'],
                    'left_player': room_state['left_player'],
                    'right_player': room_state['right_player'],
                    'current_first_player': room_state['current_first_player']
                }, room=room_id)

    @socketio.on('disconnect')
    def handle_disconnect():
        """
        處理玩家斷線
        當玩家離開時，通知房間內的其他玩家
        """
        sid = request.sid
        room_id = room_manager.leave_room(sid)
        
        if room_id:
            # 通知對手玩家已離開
            emit('opponent_left', room=room_id)


def get_winning_lines(board):
    """
    獲取獲勝的連線（座標方式）
    
    Args:
        board: 二維棋盤 [[None, 'X', ...], [...], [...]]
    
    Returns:
        list: 獲勝連線的座標列表，例如 [[[0,0], [0,1], [0,2]]]
    """
    win_conditions = [
        [[0, 0], [0, 1], [0, 2]],  # 第一行
        [[1, 0], [1, 1], [1, 2]],  # 第二行
        [[2, 0], [2, 1], [2, 2]],  # 第三行
        [[0, 0], [1, 0], [2, 0]],  # 第一列
        [[0, 1], [1, 1], [2, 1]],  # 第二列
        [[0, 2], [1, 2], [2, 2]],  # 第三列
        [[0, 0], [1, 1], [2, 2]],  # 主對角線
        [[0, 2], [1, 1], [2, 0]]   # 副對角線
    ]
    
    winning_lines = []
    for line in win_conditions:
        # 使用二維棋盤座標檢查
        pos1, pos2, pos3 = line
        if (board[pos1[0]][pos1[1]] is not None and 
            board[pos1[0]][pos1[1]] == board[pos2[0]][pos2[1]] == board[pos3[0]][pos3[1]]):
            winning_lines.append(line)
    
    return winning_lines
