# Client 與 Server Protocol

## 說明

定義前端（JavaScript/Socket.IO）與後端（Flask/Socket.IO）的通訊格式。

---

## 聊天室功能

### 送出聊天訊息

Client 傳送訊息給 Server：

```json
{
  "username": "玩家1",
  "message": "你好！",
  "time": "12:34:56"
}
```

Server 收到後會廣播給所有人，格式如下：

```json
{
  "username": "玩家1",
  "message": "你好！",
  "time": "12:34:56"
}
```

---

## 遊戲配對

### 玩家加入配對

玩家按下「開始配對」後，前端送出：

```json
{
  "action": "join_pvp"
}
```

Server 處理邏輯：

- 有等待中的房間 → 加入房間，開始遊戲
- 無等待中的房間 → 創建新房間，等待對手
- 房間已滿 → 回傳錯誤訊息

### 等待對手

Server 回傳這個表示正在等對手：

```json
{
  "room_id": "room_abcd1234_5678",
  "status": "waiting"
}
```

### 開始遊戲

兩個人都進來後，Server 會送這個：

```json
{
  "room_id": "room_abcd1234_5678",
  "your_symbol": "X", // 你是 X 還是 O
  "turn": "X", // 現在輪到誰
  "left_player": {
    // 左邊玩家
    "username": "玩家1",
    "symbol": "X"
  },
  "right_player": {
    // 右邊玩家
    "username": "玩家2",
    "symbol": "O"
  },
  "my_side": "left", // 你在左邊還是右邊
  "scores": {
    // 目前戰績
    "left": 0,
    "right": 0,
    "draw": 0
  },
  "round_count": 0 // 第幾局（0代表第1局）
}
```

備註：座位跟符號都是隨機分配的，較公平。

### 配對失敗狀況

#### 有人在玩

如果已經有其他人在玩，沒有空房間：

```json
{
  "message": "目前已有遊戲進行中，請稍後再試"
}
```

**說明：** 當前只支援一組玩家對戰，如果已有遊戲進行中，第三位玩家加入時會收到此訊息。

#### 房間已滿（極少發生）

配對時如果房間異常（同時加入導致 race condition）：

```json
{
  "message": "房間已滿，請稍後再試"
}
```

**說明：** 這是防禦性檢查，正常情況下不會發生。系統只會返回等待中且只有1位玩家的房間，理論上不會出現「找到的房間已經滿了」的情況。

---

## 下棋動作

### 玩家下棋

前端送這個告訴 Server 要下在哪：

```json
{
  "row": 1, // 第幾行 (0, 1, 2)
  "col": 1 // 第幾列 (0, 1, 2)
}
```

棋盤座標系統（使用 row, col）：

```
         col 0   col 1   col 2
row 0      □   |   □   |   □
          ---+-------+---
row 1      □   |   □   |   □
          ---+-------+---
row 2      □   |   □   |   □
```

範例：
- 正中間：`{row: 1, col: 1}`
- 左上角：`{row: 0, col: 0}`
- 右下角：`{row: 2, col: 2}`

### Server 通知下棋結果

Server 確認可以下之後，會廣播給兩個玩家：

````json
{
    "row": 1,
    "col": 1,
    "symbol": "X",     // 這格現在是 X
    "turn": "O"        // 接下來換 O
}
```只需更新該格狀態，不需傳送完整棋盤資料。


## 一回合結束通知

當連成一線或下滿了，Server 會送：
```json
{
    "winner": "X",              // X贏、O贏、或Draw平手
    "scores": {                 // 更新戰績
        "left": 1,
        "right": 0,
        "draw": 0
    },
    "round_count": 1,           // 打了幾局
    "match_finished": false,    // 5戰3勝結束了沒
    "winning_lines": [          // 連線的位置（可以畫紅線）
        [[0, 0], [0, 1], [0, 2]]
    ]
}
````

`winning_lines` 是陣列，每條線有 3 個點的座標。例如：

- 第一行：`[[0, 0], [0, 1], [0, 2]]`
- 第一列：`[[0, 0], [1, 0], [2, 0]]`
- 斜線：`[[0, 0], [1, 1], [2, 2]]`

---

## 下一局

### 開始新的一局

按下「下一局」後送出：

Server 會回傳：

````json
{
    "turn": "O",                      // 這局誰先下
    "scores": {"left": 1, "right": 0, "draw": 0},
    "round_count": 1,
    "match_finished": false,
    "current_first_player": "right"   // 這局誰先手
}
```

備註：先手會輪流（左 → 右 → 左 → 右），確保公平性。

### 重新開始5戰3勝 

備註:若今天2:2，第5戰平手，則會以平手做收。

如果5戰3勝打完了，想重新來過：

Server 會重置所有東西，分數歸零，重新分配座位和符號：
```json
{
    "turn": "X",
    "scores": {"left": 0, "right": 0, "draw": 0},
    "round_count": 0,
    "match_finished": false,
    "left_player": {
        "username": "玩家1",
        "symbol": "O"         // 符號可能跟之前不一樣
    },
    "right_player": {
        "username": "玩家2",
        "symbol": "X"
    },
    "current_first_player": "left"
}
````

---

## 其他說明

### 座標系統

改採用 `(row, col)` 格式（0-2），比原先的編號更直觀。

### 公平性機制

- **隨機分配：** 每次開始新比賽時，座位和符號會重新隨機分配
- **先手輪替：** 每局先手會輪流切換（左 → 右 → 左 → 右...）
- **目的：** 避免先手優勢固定在特定玩家

### 5戰3勝規則

- 先贏3局者獲勝
- 若 2:2 平手進入第5局，第5局若平手則整場比賽以平手收場

---

## 事件對照表

為了消除前後端在事件名稱上的歧義，下面列出後端實作中實際使用的 Socket.IO 事件名稱、方向與範例 payload，前端可依此來實作或修正現有程式。

Client → Server

- `chat message`: 傳送聊天訊息（格式參見「聊天室功能」章節）
- `join_pvp`: 加入 PVP 配對。可以傳空 payload，也可使用通用 `action` 包裝（參考下方）。
- `make_move`: 下棋，payload：`{ "row": 1, "col": 1 }`
- `reset_game`: 要求開始下一局（單回合重置）
- `start_new_match`: 用來重新開始一整場5戰3勝比賽（分數歸零、重新分配座位/符號）
- `action` (通用 wrapper): 後端同時支援一個通用的 `action` 事件，格式：`{ "action": "make_move", "data": { "row": 1, "col": 1 } }`

Server → Client

- `chat message`: 廣播聊天訊息給所有使用者(目前是以廣播進行，未針對"對戰房間")
- `waiting_for_opponent`: 當創建房間並等待對手時發回，payload：

```json
{ "room_id": "room_abcd1234_5678", "status": "waiting" }
```

- `game_start`: 當兩位玩家都加入房間後，server 會分別發送給兩位玩家（因為 `your_symbol` 和 `my_side` 每個人不同），格式：

```json
{
  "room_id": "room_abcd1234_5678",
  "your_symbol": "X",
  "turn": "X",
  "left_player": { "username": "玩家1", "symbol": "X", "sid": "..." },
  "right_player": { "username": "玩家2", "symbol": "O", "sid": "..." },
  "my_side": "left",
  "scores": { "left": 0, "right": 0, "draw": 0 },
  "round_count": 0
}
```

- `move_made`: 當一方下子成功後，server 會向該房間廣播單格更新：

```json
{ "row": 1, "col": 1, "symbol": "X", "turn": "O" }
```

- `round_end`: 當一回合結束（勝/和）時，server 廣播：

```json
{
  "winner": "X",
  "scores": { "left": 1, "right": 0, "draw": 0 },
  "round_count": 1,
  "match_finished": false,
  "winning_lines": [
    [
      [0, 0],
      [0, 1],
      [0, 2]
    ]
  ]
}
```

- `game_reset`: 下一局開始，server 廣播新局資訊（誰先下、目前分數、第幾局等）：

```json
{
  "turn": "O",                        // 這局誰先下
  "scores": { "left": 1, "right": 0, "draw": 0 },  // 目前戰績
  "round_count": 1,                   // 已經打了幾局
  "match_finished": false,            // 5戰3勝結束了沒
  "current_first_player": "right"     // 這局誰是先手方
}
```

- `new_match_started`: 當整個比賽 (5 戰 3 勝) 被重置時，server 發送新比賽資訊，payload 包含 left/right player 資訊：

```json
{
  "turn": "X",
  "scores": { "left": 0, "right": 0, "draw": 0 },
  "round_count": 0,
  "match_finished": false,
  "left_player": { "username": "玩家1", "symbol": "O" },
  "right_player": { "username": "玩家2", "symbol": "X" },
  "current_first_player": "left"
}
```

- `game_in_progress`: 配對失敗，已有遊戲進行中（詳見前述）
- `room_full`: 配對失敗，房間已滿（詳見前述）
- `opponent_left`: 對手離開房間通知
