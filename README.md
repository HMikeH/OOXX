# Tic-Tac-Toe 井字遊戲
⭕❌⭕❌ 經典井字遊戲，使用 Flask 實作，支援雙人即時對戰。

## 專案簡介
本專案以 Flask 結合 Socket.IO 實作井字棋遊戲，提供網頁介面支援雙人即時對戰（PVP），採用5戰3勝制，並透過隨機分配座位和先手輪替確保公平性。

## 功能說明
- 支援雙人即時對戰（PVP）
- 5戰3勝制，先手輪替確保公平性
- 座位和符號隨機分配
- 遊戲狀態即時同步（Socket.IO）
- 內建聊天室(廣播)
- 勝負連線動畫顯示

## 技術架構
- 前端：HTML + Flask 模板 + Socket.IO（JavaScript 即時互動）
- 後端：Flask + Flask-SocketIO + Flask-CORS
- 座標系統：二維數組 (row, col) 格式（0-2）

## 建立虛擬環境
1. 建立：`python3 -m venv venv` 或 `python -m venv venv`
2. 啟用：`source venv/bin/activate`

## 安裝模組
1. 使用 `pip install -r requirements.txt` 一次安裝所有模組

## 啟動應用程式
1. 在終端機啟用 venv 後，執行：`python WebApp.py`
2. 瀏覽器開啟：`http://localhost:5000`  可於Config調整PORT


## 查看路由
1. 執行：`flask --app WebApp routes`

## 檢查程式是否運行中
1. 執行：`sudo lsof -i :5000`

## 關閉程式
1. 執行：`sudo kill {PID}`


## 待優化方向
1. 個別聊天室（每個房間獨立聊天頻道，目前是全域廣播）
2. 支援多組對戰（目前僅限制一組玩家）
3. 增加遊戲結束後統計（勝率、對戰紀錄）
4. 前端介面美化（響應式設計、動畫效果）
5. 增加遊戲提示（音效、視覺回饋）
6. 斷線重連機制
7. 回合數可調整（3戰2勝、7戰4勝等）

## 最近更新 (2026-01-21)
1. game.py
Player(Enum) 名稱和內容不一致，Player 不要直接綁定符號（O, X）
reset() 裡的 board list 沒有重複使用，而是重新建立，沒有效率
magic number
GameResult 可再多定義 None 的情況
2. GameEvent.py
思考一下，如何不用把 socketio 傳給 GameEvent.py，也可以註冊 event 達到相同功能
handle_action() 最好把 protocol 格式定義一致，就不需要檢查是什麼型別
get_winning_lines() 應該放進 game.py 中，且 game.py 已有定義過
win_conditions list 每次都重新建立，沒有效率
3. ChatEvent.py
思考一下，如何不用把 socketio 傳給 ChatEvent.py，也可以註冊 event 達到相同功能
4. ✅ dotenv package
建議直接用 python 內建的工具取代（ex: json）
5. 登入 bug
同時開多個分頁後，然後各自輸入不同名字登入後，卻都是一樣名字和頭像
6. UI 連線垂直線畫偏了
7. 只能單機玩，無法兩台電腦對弈