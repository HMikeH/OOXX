"""
RoomManager.py - 遊戲房間管理類別
負責管理 PVP 模式的房間創建、玩家加入、遊戲狀態同步
"""

import random
from typing import Optional, Dict, List
from Game import Game, Player


class PlayerInfo:
    """玩家資訊類別 - 儲存單一玩家的連線資料"""
    
    def __init__(self, sid: str, username: str, symbol: str):
        """
        建立玩家實例
        
        Args:
            sid : Socket ID - 玩家的 Socket 連線編號，用於識別玩家
            username : 玩家名稱 - 在遊戲介面上顯示的名字
            symbol : 玩家符號 - 'X' 或 'O'（初始可能是 'TEMP' 待分配）
        """
        self.sid = sid
        self.username = username
        self.symbol = symbol
    
    def to_dict(self) -> dict:
        """轉成 dict 方便傳給前端"""
        return {
            'sid': self.sid,
            'username': self.username,
            'symbol': self.symbol
        }


class GameRoom:
    """
    遊戲房間類別
    管理一個房間內的：
    - 遊戲狀態（棋盤、輪次、勝者）
    - 玩家資訊（座位、符號分配）
    - 比賽統計（5戰3勝的戰績）
    """
    
    def __init__(self, room_id: str, creator_sid: str, creator_username: str):
        """
        初始化遊戲房間
        
        Args:
            room_id : 房間 ID - 唯一識別房間的編號
            creator_sid: 創建者 Socket ID - 第一位玩家
            creator_username : 創建者名稱 - 第一位玩家的名字
        """
        self.room_id = room_id
        self.game = Game()  # 遊戲實例
        self.players: List[PlayerInfo] = [] # 玩家列表，最多兩位
        self.waiting = True  # 等待第二位玩家
        
        # 【重要】5戰3勝制度的統計資料
        self.scores = {
            'left': 0,      # 左邊玩家贏的局數
            'right': 0,     # 右邊玩家贏的局數
            'draw': 0       # 平局的局數
        }
        self.round_count = 0          # 當前進行到第幾回合（0-4，總共5回合）
        self.match_finished = False   # 比賽是否已完全結束（5戰結束或某方先達3勝，或達到5局未分出勝負。）
        self.current_first_player = 'left'  # 當前回合的先手玩家 ('left' 或 'right')
        
        # 座位和符號分配（會由_assign_seats_and_symbols() 隨機決定）
        self.left_player = None   # 坐在左邊的玩家
        self.right_player = None  # 坐在右邊的玩家
        
        # 先用臨時符號創建第一位玩家，等第二位加入後再隨機分配
        first_player = PlayerInfo(creator_sid, creator_username, 'TEMP')
        self.players.append(first_player)
    
    def add_player(self, sid: str, username: str) -> bool:
        """
        添加第二位玩家到房間
        當第二位玩家加入後，自動隨機分配座位和符號，並開始遊戲
        
        Args:
            sid: 玩家 Socket ID
            username: 玩家名稱
            
        Returns:
            bool: True=成功添加，False=房間已滿（已有2位玩家）
        """
        # 檢查房間是否已滿
        if len(self.players) >= 2:
            return False
        
        # 用臨時符號創建第二位玩家
        second_player = PlayerInfo(sid, username, 'TEMP')
        self.players.append(second_player)
        self.waiting = False  # 停止等待，因為已有兩位玩家
        
        # 兩位玩家都到齊了，隨機分配座位（左/右）和符號（X/O）
        self._assign_seats_and_symbols()
        
        # 開始遊戲
        self.game.start()
        return True
    
    def remove_player(self, sid: str) -> bool:
        """
        移除玩家
        
        Args:
            sid: 玩家 Socket ID
            
        Returns:
            bool: 是否成功移除
        """
        for player in self.players:
            if player.sid == sid:
                self.players.remove(player)
                return True
        return False
    
    def get_player_by_sid(self, sid: str) -> Optional[PlayerInfo]:
        """
        根據 Socket ID 獲取玩家資訊
        
        Args:
            sid: Socket ID
            
        Returns:
            Optional[PlayerInfo]: 找到則返回玩家資訊，否則返回 None
        """
        for player in self.players:
            if player.sid == sid:
                return player
        return None
    
    def _assign_seats_and_symbols(self):
        """
        隨機分配玩家座位和符號
        
        分配邏輯：
        1. 隨機決定誰坐左邊、誰坐右邊
        2. 隨機決定 X 和 O 符號分配給左右玩家
        3. 更新玩家列表中的符號值，確保引用一致
        """
        # 步驟1：隨機打亂玩家順序，決定座位
        shuffled = random.sample(self.players, 2)
        self.left_player = shuffled[0]   # 隨機選中的玩家坐左邊
        self.right_player = shuffled[1]  # 另一位玩家坐右邊
        
        # 步驟2：隨機決定符號分配
        symbols = random.sample([Player.X.value, Player.O.value], 2)
        self.left_player.symbol = symbols[0]   # 左邊玩家獲得第一個符號
        self.right_player.symbol = symbols[1]  # 右邊玩家獲得第二個符號
        
        # 步驟3：同步更新到玩家列表
        # 確保 self.players 中的符號與 left_player 和 right_player 的值一致
        for player in self.players:
            if player.sid == self.left_player.sid:
                player.symbol = self.left_player.symbol
            elif player.sid == self.right_player.sid:
                player.symbol = self.right_player.symbol
    
    def make_move(self, sid: str, row: int, col: int) -> bool:
        """
        執行移動（使用座標方式）
        
        Args:
            sid: 玩家 Socket ID
            row: 行座標 (0-2)
            col: 列座標 (0-2)
            
        Returns:
            bool: 移動是否成功
        """
        # 獲取玩家資訊
        player = self.get_player_by_sid(sid)
        if not player:
            return False
        
        # 檢查是否輪到該玩家
        if self.game.turn != player.symbol:
            return False
        
        # 執行移動（直接使用座標）
        return self.game.make_move(row, col, player.symbol)
    
    def reset(self):
        """重置遊戲（新的一回合）"""
        # 檢查是否已經結束比賽
        if self.match_finished:
            return
        
        # 先檢查當前比賽狀態是否已達結束條件
        if self.scores['left'] >= 3 or self.scores['right'] >= 3:
            self.match_finished = True
            return
        
        # 檢查是否已經打完5戰（round_count 從0開始，打完第5戰時 round_count == 4）
        if self.round_count >= 4:
            self.match_finished = True
            return
        
        # 增加回合數（開始新的一回合）
        self.round_count += 1
        
        # 輪替先手
        self.current_first_player = 'right' if self.current_first_player == 'left' else 'left'
        
        # 設定先手符號
        if self.current_first_player == 'left':
            first_symbol = self.left_player.symbol
        else:
            first_symbol = self.right_player.symbol
        
        # 重置棋盤和遊戲狀態
        self.game.reset()
        self.game.turn = first_symbol
        self.game.started = True
    
    def check_round_end(self) -> bool:
        """檢查回合是否結束並更新戰績"""
        if self.game.winner:
            # 根據勝者類型統計分數
            if self.game.winner == 'Draw':
                self.scores['draw'] += 1  # 平局次數
            elif self.game.winner == self.left_player.symbol:
                self.scores['left'] += 1  # 左邊玩家勝場數
            elif self.game.winner == self.right_player.symbol:
                self.scores['right'] += 1  # 右邊玩家勝場數
            
            # 檢查比賽是否已結束
            if self.scores['left'] >= 3 or self.scores['right'] >= 3:
                # 某方已達 3 勝，比賽結束
                self.match_finished = True
            elif self.round_count >= 4:
                # 已完成第 5 回合（round_count 從 0 開始計算）
                # 第1回合結束時 round_count=0，第5回合結束時 round_count=4
                self.match_finished = True
            
            return True
        return False
    
    def get_state(self) -> dict:
        """
        獲取房間狀態
        
        Returns:
            dict: 包含房間、玩家、遊戲狀態
        """
        return {
            'room_id': self.room_id,
            'players': [player.to_dict() for player in self.players],
            'board': self.game.board,
            'turn': self.game.turn,
            'winner': self.game.winner,
            'waiting': self.waiting,
            'started': self.game.started,
            'scores': self.scores,  # 5戰3勝的戰績統計
            'round_count': self.round_count,
            'match_finished': self.match_finished,
            'current_first_player': self.current_first_player,
            'left_player': self.left_player.to_dict() if self.left_player else None,
            'right_player': self.right_player.to_dict() if self.right_player else None
        }


class RoomManager:
    """
    房間管理器類別
    負責管理所有遊戲房間和玩家對應關係
    """
    
    def __init__(self):
        """初始化房間管理器"""
        # 房間字典：{room_id: GameRoom}
        self.rooms: Dict[str, GameRoom] = {}
        # 玩家到房間的映射：{sid: room_id}
        self.player_to_room: Dict[str, str] = {}
    
    def create_room(self, sid: str, username: str) -> str:
        """
        創建新房間
        
        Args:
            sid: 創建者 Socket ID
            username: 創建者名稱
            
        Returns:
            str: 房間 ID
        """
        # 生成唯一房間 ID
        room_id = f"room_{sid[:8]}_{random.randint(1000, 9999)}" # eg. room_abcd1234_5678
        
        # 創建房間
        room = GameRoom(room_id, sid, username)
        self.rooms[room_id] = room
        self.player_to_room[sid] = room_id
        
        return room_id
    
    def join_room(self, room_id: str, sid: str, username: str) -> bool:
        """
        加入現有房間
        
        Args:
            room_id: 房間 ID
            sid: 玩家 Socket ID
            username: 玩家名稱
            
        Returns:
            bool: 是否成功加入
        """
        if room_id not in self.rooms:
            return False
        
        room = self.rooms[room_id]
        success = room.add_player(sid, username)
        
        if success:
            self.player_to_room[sid] = room_id
        
        return success
    
    def leave_room(self, sid: str) -> Optional[str]:
        """
        離開房間
        
        Args:
            sid: 玩家 Socket ID
            
        Returns:
            Optional[str]: 房間 ID，若玩家不在任何房間則返回 None
        """
        room_id = self.player_to_room.get(sid)
        if not room_id:
            return None
        
        room = self.rooms.get(room_id)
        if room:
            room.remove_player(sid)
            # 如果房間為空或只剩一人，刪除房間
            if len(room.players) <= 1:
                # 如果還有一人，也要移除他的映射
                for player in room.players:
                    if player.sid in self.player_to_room:
                        del self.player_to_room[player.sid]
                del self.rooms[room_id]
        
        if sid in self.player_to_room:
            del self.player_to_room[sid]
        return room_id
    
    def get_room_count(self) -> int:
        """
        獲取當前房間數量
        
        Returns:
            int: 房間數量
        """
        return len(self.rooms)
    
    def get_waiting_room_count(self) -> int:
        """
        獲取等待中的房間數量
        
        Returns:
            int: 等待中的房間數量
        """
        return sum(1 for room in self.rooms.values() if room.waiting)
    
    def get_active_room_count(self) -> int:
        """
        獲取進行中的房間數量
        
        Returns:
            int: 進行中的房間數量
        """
        return sum(1 for room in self.rooms.values() if not room.waiting)
    
    def get_active_game_count(self) -> int:
        """
        獲取正在進行的遊戲數量（必須有兩個玩家且遊戲已開始）
        
        Returns:
            int: 正在進行的遊戲數量
        """
        return sum(1 for room in self.rooms.values() 
                  if len(room.players) == 2 and room.game.started and not room.waiting)
    
    def get_available_room(self) -> Optional[str]:
        """
        獲取一個等待中的房間
        
        Returns:
            Optional[str]: 房間 ID，若無可用房間則返回 None
        """
        for room_id, room in self.rooms.items():
            if room.waiting and len(room.players) == 1:
                return room_id
        return None
    
    def get_room(self, room_id: str) -> Optional[GameRoom]:
        """
        獲取房間實例
        
        Args:
            room_id: 房間 ID
            
        Returns:
            Optional[GameRoom]: 房間實例，若不存在則返回 None
        """
        return self.rooms.get(room_id)
    
    def get_room_by_sid(self, sid: str) -> Optional[str]:
        """
        根據玩家 Socket ID 獲取房間 ID
        
        Args:
            sid: 玩家 Socket ID
            
        Returns:
            Optional[str]: 房間 ID，若玩家不在任何房間則返回 None
        """
        return self.player_to_room.get(sid)
    
    def make_move(self, room_id: str, sid: str, row: int, col: int) -> Optional[dict]:
        """
        在指定房間執行移動（使用座標方式）
        
        Args:
            room_id: 房間 ID
            sid: 玩家 Socket ID
            row: 行座標 (0-2)
            col: 列座標 (0-2)
            
        Returns:
            Optional[dict]: 更新後的房間狀態，若失敗則返回 None
        """
        room = self.get_room(room_id)
        if not room:
            return None
        
        success = room.make_move(sid, row, col)
        if not success:
            return None
        
        # 檢查回合是否結束
        room.check_round_end()
        
        return room.get_state()
    
    def reset_room(self, room_id: str) -> Optional[dict]:
        """
        重置指定房間的遊戲
        
        Args:
            room_id: 房間 ID
            
        Returns:
            Optional[dict]: 重置後的房間狀態，若房間不存在則返回 None
        """
        room = self.get_room(room_id)
        if not room:
            return None
        
        room.reset()
        return room.get_state()
