/**
 * 井字棋遊戲前端邏輯
 * 處理 Socket.IO 通訊、遊戲狀態和 UI 更新
 */

// 全域變數
const socket = io();
let chatMessages, chatInput, chatSend, gameBoard, resetBtn;

// 遊戲狀態
let mySymbol = null;
let currentTurn = "X";
let gameActive = false;
let mySide = null; // 'left' or 'right'
let leftPlayer = null;
let rightPlayer = null;
let scores = { left: 0, right: 0, draw: 0 };
let roundCount = 0;
let matchFinished = false;
let board = [[null, null, null], [null, null, null], [null, null, null]];

/**
 * 初始化遊戲
 * 頁面完成後自動載入
 */
function initGame() {
  // 抓取所有需要的 DOM 元素
  chatMessages = document.getElementById("chat-messages");
  chatInput = document.getElementById("chat-input");
  chatSend = document.getElementById("chat-send");
  gameBoard = document.getElementById("game-board");
  resetBtn = document.getElementById("reset-btn");

  // 一開始先把棋盤鎖住，等配對成功再解鎖
  if (gameBoard) {
    const cells = gameBoard.querySelectorAll(".cell");
    cells.forEach((cell) => {
      cell.disabled = true;
      cell.textContent = "";
    });
  }

  // 設置聊天室相關事件監聽
  setupChatEvents();

  // 設置遊戲相關 socket 事件監聽
  setupPvPEvents();
  // 進來就直接開始配對（使用 proto 中定義的 action JSON 格式）
  socket.emit("action", { action: "join_pvp" });
}

/**
 * 設置聊天室相關事件
 */
function setupChatEvents() {
  if (chatInput) {
    chatInput.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        chatSend.click();
      }
    });
  }

  socket.on("chat message", function (msg) {
    // 使用統一的系統提示格式
    if (msg && typeof msg === "object" && msg.username === "系統") {
      appendMessage("[系統提示] " + (msg.message || ""));
    } else {
      appendMessage(msg);
    }
  });
}

/**
 * 設置 PvP 模式事件監聽
 */
function setupPvPEvents() {
  // 遊戲進行中事件
  socket.on("game_in_progress", function (data) {
    const waitingAnimation = document.querySelector(".waiting-animation");
    if (waitingAnimation) {
      waitingAnimation.style.display = "none";
    }

    appendMessage("[系統提示] " + data.message);

    // 顯示提示訊息
    const pvpInfo = document.querySelector(".pvp-info");
    if (pvpInfo) {
      pvpInfo.innerHTML = `
                <div style="padding: 40px 20px; text-align: center;">
                    <div style="font-size: 48px; margin-bottom: 20px;">🎮</div>
                    <div style="font-size: 20px; font-weight: bold; color: #FF6B6B; margin-bottom: 10px;">
                        遊戲進行中
                    </div>
                    <div style="font-size: 14px; color: #666; margin-bottom: 20px;">
                        目前已有玩家正在對戰，請稍後再試
                    </div>
                    <button onclick="location.reload()" style="padding: 10px 20px; font-size: 14px; background: #333; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        重新嘗試
                    </button>
                </div>
            `;
    }
  });

  // 房間已滿事件
  socket.on("room_full", function (data) {
    updateGameStatus(data.message, "error");
    appendMessage("[系統提示] " + data.message);
  });

  // 等待對手事件（不需要顯示文字，已在HTML中顯示）
  socket.on("waiting_for_opponent", function (data) {
    // 等待動畫已經在顯示了，不需要額外的狀態文字
  });

  // 遊戲開始事件
  socket.on("game_start", function (data) {
    // 隱藏配對區和等待動畫
    const pvpInfo = document.querySelector(".pvp-info");
    if (pvpInfo) pvpInfo.style.display = "none";

    leftPlayer = data.left_player;
    rightPlayer = data.right_player;
    mySide = data.my_side;
    mySymbol = data.your_symbol;
    currentTurn = data.turn;
    scores = data.scores;
    roundCount = data.round_count;
    gameActive = true;
    board = [[null, null, null], [null, null, null], [null, null, null]];

    // 顯示戰績板和棋盤
    const scoreBoard = document.getElementById("score-board");
    if (scoreBoard) scoreBoard.classList.add("active");

    if (gameBoard) {
      gameBoard.classList.add("active");
    }
    if (resetBtn) {
      resetBtn.classList.add("visible");
      resetBtn.textContent = "下一回合";
    }

    clearBoard();
    updateTurnDisplay();
    updateScoreDisplay();
  });

  // 移動完成事件
  socket.on("move_made", function (data) {
    // 使用二維數組座標直接訪問
    board[data.row][data.col] = data.symbol;
    updateCell(data.row, data.col, data.symbol);
    currentTurn = data.turn;
    updateTurnDisplay();
  });

  // 回合結束事件
  socket.on("round_end", function (data) {
    gameActive = false;
    scores = data.scores;
    roundCount = data.round_count;
    matchFinished = data.match_finished;

    // 繪製連線
    if (data.winning_lines && data.winning_lines.length > 0) {
      drawWinningLines(data.winning_lines);
    }

    // 禁用所有格子
    if (gameBoard) {
      const cells = gameBoard.querySelectorAll(".cell");
      cells.forEach((cell) => (cell.disabled = true));
    }

    updateScoreDisplay();

    // 如果比賽已結束，直接顯示最終結果
    if (matchFinished) {
      let finalMessage = "";
      let winnerName = "";
      if (scores.left >= 3) {
        winnerName = leftPlayer.username;
        finalMessage = `🎉 ${leftPlayer.username} (${leftPlayer.symbol}) 獲勝！比分 ${scores.left}:${scores.right}`;
      } else if (scores.right >= 3) {
        winnerName = rightPlayer.username;
        finalMessage = `🎉 ${rightPlayer.username} (${rightPlayer.symbol}) 獲勝！比分 ${scores.right}:${scores.left}`;
      } else if (scores.left > scores.right) {
        // 5回合結束，左邊分數較高
        winnerName = leftPlayer.username;
        finalMessage = `🎉 ${leftPlayer.username} (${leftPlayer.symbol}) 獲勝！比分 ${scores.left}:${scores.right}`;
      } else if (scores.right > scores.left) {
        // 5回合結束，右邊分數較高
        winnerName = rightPlayer.username;
        finalMessage = `🎉 ${rightPlayer.username} (${rightPlayer.symbol}) 獲勝！比分 ${scores.right}:${scores.left}`;
      } else {
        // 分數相同才是平手
        finalMessage = `🤝 比賽結束！雙方戰成 ${scores.left}:${scores.right} 平手！`;
      }

      updateGameStatus(finalMessage, "win");

      // 在聊天室顯示系統提示
      if (winnerName) {
        appendMessage(`[系統提示] 🏆 ${winnerName} 主宰了比賽！`);
      } else {
        appendMessage(`[系統提示] ${finalMessage}`);
      }

      if (resetBtn) {
        resetBtn.textContent = "下一輪";
        resetBtn.disabled = false;
      }
    } else {
      // 比賽未結束，顯示本回合結果
      if (data.winner === "Draw") {
        updateGameStatus("平手！", "draw");
      } else {
        // 判斷誰贏了
        const mySymbol = mySide === "left" ? leftPlayer.symbol : rightPlayer.symbol;
        const iWon = (data.winner === mySymbol);

        if (iWon) {
          updateGameStatus("你贏了！🎉", "win");
        } else {
          updateGameStatus("你輸了！", "lose");
        }
      }

      if (resetBtn) {
        resetBtn.textContent = "下一回合";
        resetBtn.disabled = false;
      }
    }
  });

  // 遊戲重置事件
  socket.on("game_reset", function (data) {
    currentTurn = data.turn;
    scores = data.scores;
    roundCount = data.round_count;
    matchFinished = data.match_finished;

    // 如果比賽已經結束，顯示最終結果
    if (matchFinished) {
      gameActive = false;

      // 更新分數顯示
      updateScoreDisplay();

      // 顯示最終結果
      let finalMessage = "";
      if (scores.left >= 3) {
        finalMessage = `比賽結束！${leftPlayer.username} (${leftPlayer.symbol}) 以 ${scores.left}:${scores.right} 獲勝！`;
      } else if (scores.right >= 3) {
        finalMessage = `比賽結束！${rightPlayer.username} (${rightPlayer.symbol}) 以 ${scores.right}:${scores.left} 獲勝！`;
      } else if (scores.left === 2 && scores.right === 2) {
        finalMessage = "比賽結束！雙方戰成 2:2 平手！";
      }

      if (finalMessage) {
        updateGameStatus(finalMessage, "win");
      }

      // 更新按鈕
      if (resetBtn) {
        resetBtn.textContent = "下一輪";
        resetBtn.disabled = false;
      }

      return; // 不執行重置棋盤的操作
    }

    // 正常開始新回合
    gameActive = true;
    board = [[null, null, null], [null, null, null], [null, null, null]];

    clearBoard();
    clearWinningLines();
    updateScoreDisplay();
    updateTurnDisplay();

    // 重新啟用按鈕（下一回合開始後禁用）
    if (resetBtn) {
      resetBtn.disabled = true;
    }
  });

  // 新比賽開始事件
  socket.on("new_match_started", function (data) {
    // 更新玩家資訊（可能重新分配了座位和符號）
    leftPlayer = data.left_player;
    rightPlayer = data.right_player;

    // 更新我的符號和位置（因為可能重新分配了）
    const mySid = socket.id;
    if (leftPlayer.sid === mySid) {
      mySide = "left";
      mySymbol = leftPlayer.symbol;
    } else if (rightPlayer.sid === mySid) {
      mySide = "right";
      mySymbol = rightPlayer.symbol;
    }

    // 重置所有狀態
    currentTurn = data.turn;
    scores = data.scores;
    roundCount = data.round_count;
    matchFinished = data.match_finished;
    gameActive = true;
    board = [[null, null, null], [null, null, null], [null, null, null]];

    // 更新UI
    clearBoard();
    clearWinningLines();
    updateScoreDisplay();
    updateTurnDisplay();

    // 更新按鈕
    if (resetBtn) {
      resetBtn.textContent = "下一回合";
      resetBtn.disabled = true;
    }
  });

  // 對手離開事件
  socket.on("opponent_left", function () {
    gameActive = false;
    matchFinished = true;

    // 隱藏遊戲狀態提示（清除「你輸了！」等訊息）
    const gameStatus = document.getElementById("game-status");
    if (gameStatus) {
      gameStatus.classList.remove("active");
      gameStatus.textContent = "";
    }

    // 隱藏戰績板和棋盤
    const scoreBoard = document.getElementById("score-board");
    if (scoreBoard) scoreBoard.classList.remove("active");
    if (gameBoard) gameBoard.classList.remove("active");

    // 隱藏重置按鈕
    if (resetBtn) {
      resetBtn.classList.remove("visible");
    }

    // 重新顯示等待動畫
    const pvpInfo = document.querySelector(".pvp-info");
    if (pvpInfo) {
      pvpInfo.style.display = "block";
      pvpInfo.innerHTML = `
                <div class="waiting-animation">
                    <div class="waiting-spinner">
                        <div class="spinner-dot"></div>
                        <div class="spinner-dot"></div>
                        <div class="spinner-dot"></div>
                    </div>
                    <div class="waiting-text">等待對手加入</div>
                    <div class="waiting-subtext">正在配對中...</div>
                </div>
            `;
    }

    appendMessage("[系統提示] 您的對手已離開，正在尋找新對手...");

    // 重置遊戲狀態
    mySymbol = null;
    mySide = null;
    leftPlayer = null;
    rightPlayer = null;
    scores = { left: 0, right: 0, draw: 0 };
    roundCount = 0;
    board = [[null, null, null], [null, null, null], [null, null, null]];

    // 自動重新配對（使用 action JSON 格式）
    setTimeout(function () {
      socket.emit("action", { action: "join_pvp" });
    }, 1000);
  });

  // 處理棋盤點擊事件（使用座標方式）
  if (gameBoard) {
    gameBoard.addEventListener("click", function (e) {
      if (e.target.classList.contains("cell")) {
        const cellIndex = parseInt(e.target.dataset.cell);
        const row = Math.floor(cellIndex / 3);
        const col = cellIndex % 3;

        if (
          gameActive &&
          currentTurn === mySymbol &&
          !e.target.disabled &&
          board[row][col] === null
        ) {
          socket.emit("make_move", { row: row, col: col });
        }
      }
    });
  }
}

/**
 * 聊天室功能
 */
function appendMessage(msg) {
  if (chatMessages) {
    const div = document.createElement("div");
    // 支援字串或結構化物件 { username, message, time }
    if (typeof msg === "string") {
      div.textContent = msg;
    } else if (msg && typeof msg === "object") {
      const user = msg.username || "匿名";
      const time = msg.time || "";
      const message = msg.message || "";
      div.textContent = time
        ? `[${time}] ${user}: ${message}`
        : `${user}: ${message}`;
    } else {
      div.textContent = String(msg);
    }
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
}

function sendMessage() {
  const msg = chatInput.value.trim();
  if (msg) {
    // 以結構化 JSON 送出，伺服器會以 session 的 username 覆蓋或填入
    const timestamp = new Date().toLocaleTimeString("zh-TW", { hour12: false });
    socket.emit("chat message", { message: msg, time: timestamp });
    chatInput.value = "";
  }
}

/**
 * 遊戲控制功能
 */
function resetGame() {
  // 禁用按鈕，避免重複點擊
  if (resetBtn) {
    resetBtn.disabled = true;
  }

  if (matchFinished) {
    // 比賽結束，開始新的一輪
    socket.emit("start_new_match");
  } else {
    // 下一回合
    socket.emit("reset_game");
  }
}

/**
 * 棋盤更新功能
 */
function clearBoard() {
  if (!gameBoard) return;
  const cells = gameBoard.querySelectorAll(".cell");
  cells.forEach((cell) => {
    cell.textContent = "";
    cell.disabled = false;
  });
}

function updateCell(row, col, symbol) {
  if (!gameBoard) return;
  const cellIndex = row * 3 + col;
  const cells = gameBoard.querySelectorAll(".cell");
  if (cells[cellIndex]) {
    cells[cellIndex].textContent = symbol || "";
    cells[cellIndex].disabled = symbol !== null;
  }
}

/**
 * UI 顯示更新功能
 */
function updateGameStatus(message, type = "") {
  const gameStatus = document.getElementById("game-status");
  if (gameStatus) {
    gameStatus.textContent = message;
    gameStatus.className = "game-status active " + type;
  }
}

function updateTurnDisplay() {
  if (gameActive) {
    if (currentTurn === mySymbol) {
      updateGameStatus("YOUR TURN!!", "turn");
    } else {
      updateGameStatus("對手回合...", "waiting");
    }
  }
}

function updateScoreDisplay() {
  // 更新左玩家
  const leftSymbolEl = document.getElementById("left-symbol");
  const leftNameEl = document.getElementById("left-name");
  const leftScoreEl = document.getElementById("left-score");

  if (leftPlayer && leftSymbolEl && leftNameEl && leftScoreEl) {
    leftSymbolEl.textContent = leftPlayer.symbol;
    leftNameEl.textContent = leftPlayer.username;
    leftScoreEl.textContent = scores.left;
  }

  // 更新右玩家
  const rightSymbolEl = document.getElementById("right-symbol");
  const rightNameEl = document.getElementById("right-name");
  const rightScoreEl = document.getElementById("right-score");

  if (rightPlayer && rightSymbolEl && rightNameEl && rightScoreEl) {
    rightSymbolEl.textContent = rightPlayer.symbol;
    rightNameEl.textContent = rightPlayer.username;
    rightScoreEl.textContent = scores.right;
  }

  // 更新回合和平手
  const roundInfoEl = document.getElementById("round-info");
  const drawScoreEl = document.getElementById("draw-score");

  if (roundInfoEl) {
    roundInfoEl.textContent = `回合 ${roundCount + 1}/5`;
  }

  if (drawScoreEl) {
    drawScoreEl.textContent = scores.draw;
  }
}

/**
 * 連線繪製功能
 */
function drawWinningLines(winningLines) {
  // 清除之前的連線
  clearWinningLines();

  if (!gameBoard) return;

  // 為每條連線繪製線條
  winningLines.forEach((line, index) => {
    const canvas = document.createElement("canvas");
    canvas.className = "winning-line";
    canvas.style.position = "absolute";
    canvas.style.top = "0";
    canvas.style.left = "0";
    canvas.style.width = "100%";
    canvas.style.height = "100%";
    canvas.style.pointerEvents = "none";
    canvas.style.zIndex = "10";

    gameBoard.style.position = "relative";
    gameBoard.appendChild(canvas);

    const rect = gameBoard.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;

    const ctx = canvas.getContext("2d");
    const cellWidth = rect.width / 3;
    const cellHeight = rect.height / 3;

    // 起點和終點
    const startRow = line[0][0];
    const startCol = line[0][1];
    const endRow = line[2][0];
    const endCol = line[2][1];

    const startX = (startCol + 0.5) * cellWidth;
    const startY = (startRow + 0.5) * cellHeight;
    const endX = (endCol + 0.5) * cellWidth;
    const endY = (endRow + 0.5) * cellHeight;

    // 繪製線條
    ctx.strokeStyle = "#FF5722";
    ctx.lineWidth = 5;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(startX, startY);
    ctx.lineTo(endX, endY);
    ctx.stroke();
  });
}

function clearWinningLines() {
  if (!gameBoard) return;
  const lines = gameBoard.querySelectorAll(".winning-line");
  lines.forEach((line) => line.remove());
}
