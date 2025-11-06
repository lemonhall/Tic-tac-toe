// UI Manager - 管理界面更新和渲染
export class UIManager {
    constructor() {
        this.elements = {
            // 棋盘
            board: document.getElementById('game-board'),
            cells: document.querySelectorAll('.cell'),
            winLine: document.getElementById('win-line'),
            
            // 控制按钮
            startBtn: document.getElementById('start-game-btn'),
            resetBtn: document.getElementById('reset-game-btn'),
            pauseBtn: document.getElementById('pause-game-btn'),
            
            // 模式选择
            modeBtns: document.querySelectorAll('.mode-btn'),
            playerXSelect: document.getElementById('player-x-type'),
            playerOSelect: document.getElementById('player-o-type'),
            
            // 状态显示
            gameId: document.getElementById('game-id'),
            currentTurn: document.getElementById('current-turn'),
            gameStatus: document.getElementById('game-status'),
            currentPlayerText: document.getElementById('current-player-text'),
            connectionIndicator: document.getElementById('connection-indicator'),
            connectionText: document.getElementById('connection-text'),
            gameMessage: document.getElementById('game-message'),
            
            // 历史和统计
            moveHistory: document.getElementById('move-history'),
            xWins: document.getElementById('x-wins'),
            oWins: document.getElementById('o-wins'),
            draws: document.getElementById('draws'),
            
            // 模态框
            modal: document.getElementById('game-over-modal'),
            modalTitle: document.getElementById('modal-title'),
            modalMessage: document.getElementById('modal-message'),
            modalNewGame: document.getElementById('modal-new-game'),
            modalClose: document.getElementById('modal-close')
        };
    }

    // 渲染棋盘
    renderBoard(board) {
        this.elements.cells.forEach((cell, index) => {
            const row = Math.floor(index / 3);
            const col = index % 3;
            const value = board[row][col];
            
            cell.textContent = value || '';
            cell.className = 'cell';
            
            if (value) {
                cell.classList.add('occupied', value.toLowerCase());
            }
        });
    }

    // 更新单个格子
    updateCell(row, col, value) {
        const index = row * 3 + col;
        const cell = this.elements.cells[index];
        
        cell.textContent = value;
        cell.classList.add('occupied', value.toLowerCase());
    }

    // 显示获胜线条
    showWinningLine(winningLine) {
        if (!winningLine || winningLine.length !== 2) return;
        
        const [start, end] = winningLine;
        const cellSize = this.elements.cells[0].offsetWidth;
        const gap = 10;
        const padding = 10;
        
        // 计算线条坐标
        const x1 = padding + start[1] * (cellSize + gap) + cellSize / 2;
        const y1 = padding + start[0] * (cellSize + gap) + cellSize / 2;
        const x2 = padding + end[1] * (cellSize + gap) + cellSize / 2;
        const y2 = padding + end[0] * (cellSize + gap) + cellSize / 2;
        
        const line = this.elements.winLine.querySelector('line');
        line.setAttribute('x1', x1);
        line.setAttribute('y1', y1);
        line.setAttribute('x2', x2);
        line.setAttribute('y2', y2);
        
        this.elements.winLine.classList.add('show');
        
        // 高亮获胜的格子
        for (let i = 0; i < 3; i++) {
            const row = start[0] + i * (end[0] - start[0]) / 2;
            const col = start[1] + i * (end[1] - start[1]) / 2;
            const index = Math.round(row) * 3 + Math.round(col);
            this.elements.cells[index].classList.add('winning');
        }
    }

    // 隐藏获胜线条
    hideWinningLine() {
        this.elements.winLine.classList.remove('show');
        this.elements.cells.forEach(cell => {
            cell.classList.remove('winning');
        });
    }

    // 更新游戏信息
    updateGameInfo(gameId, currentPlayer, status) {
        this.elements.gameId.textContent = gameId || '-';
        this.elements.currentTurn.textContent = currentPlayer || '-';
        this.elements.gameStatus.textContent = this.getStatusText(status);
    }

    // 更新当前玩家显示
    updateCurrentPlayer(player, playerType) {
        const typeText = {
            'human': '人类',
            'ai': 'AI',
            'agent': 'Agent'
        };
        
        const playerEmoji = player === 'X' ? '❌' : '⭕';
        this.elements.currentPlayerText.textContent = 
            `当前回合: ${playerEmoji} 玩家${player} (${typeText[playerType] || playerType})`;
    }

    // 更新连接状态
    updateConnectionStatus(status) {
        const indicator = this.elements.connectionIndicator;
        const text = this.elements.connectionText;
        
        indicator.className = 'status-dot';
        
        switch(status) {
            case 'connected':
                indicator.classList.add('connected');
                text.textContent = '已连接';
                break;
            case 'connecting':
                indicator.classList.add('connecting');
                text.textContent = '连接中...';
                break;
            case 'disconnected':
                indicator.classList.add('disconnected');
                text.textContent = '未连接';
                break;
        }
    }

    // 显示消息
    showMessage(message, type = 'info') {
        const messageBox = this.elements.gameMessage.parentElement;
        messageBox.className = 'message-box';
        
        if (type !== 'info') {
            messageBox.classList.add(type);
        }
        
        this.elements.gameMessage.textContent = message;
    }

    // 添加移动到历史
    addMoveToHistory(move) {
        const moveItem = document.createElement('div');
        moveItem.className = 'move-item';
        
        moveItem.innerHTML = `
            <div>
                <span class="move-number">#${move.moveNumber}</span>
                <span class="move-player ${move.player.toLowerCase()}">
                    玩家${move.player}
                </span>
            </div>
            <span class="move-position">
                (${move.row}, ${move.col})
            </span>
        `;
        
        this.elements.moveHistory.insertBefore(
            moveItem, 
            this.elements.moveHistory.firstChild
        );
    }

    // 清空移动历史
    clearMoveHistory() {
        this.elements.moveHistory.innerHTML = '';
    }

    // 更新统计数据
    updateStats(stats) {
        this.elements.xWins.textContent = stats.xWins;
        this.elements.oWins.textContent = stats.oWins;
        this.elements.draws.textContent = stats.draws;
    }

    // 显示游戏结束模态框
    showGameOverModal(winner, isDraw) {
        let title, message;
        
        if (isDraw) {
            title = '平局！';
            message = '棋盘已满，这局是平局！';
        } else {
            title = `玩家 ${winner} 获胜！`;
            message = `🎉 恭喜玩家 ${winner} 赢得了这局游戏！`;
        }
        
        this.elements.modalTitle.textContent = title;
        this.elements.modalMessage.textContent = message;
        this.elements.modal.classList.add('show');
    }

    // 隐藏模态框
    hideGameOverModal() {
        this.elements.modal.classList.remove('show');
    }

    // 禁用/启用棋盘
    setBoardEnabled(enabled) {
        this.elements.cells.forEach(cell => {
            if (enabled) {
                cell.classList.remove('disabled');
            } else {
                cell.classList.add('disabled');
            }
        });
    }

    // 设置模式按钮激活状态
    setActiveMode(mode) {
        this.elements.modeBtns.forEach(btn => {
            if (btn.dataset.mode === mode) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    }

    // 获取玩家类型选择
    getPlayerTypes() {
        return {
            playerX: this.elements.playerXSelect.value,
            playerO: this.elements.playerOSelect.value
        };
    }

    // 设置玩家类型
    setPlayerTypes(playerX, playerO) {
        this.elements.playerXSelect.value = playerX;
        this.elements.playerOSelect.value = playerO;
    }

    // 获取状态文本
    getStatusText(status) {
        const statusMap = {
            'not_started': '未开始',
            'in_progress': '进行中',
            'finished': '已结束'
        };
        return statusMap[status] || status;
    }

    // 设置按钮状态
    setButtonEnabled(button, enabled) {
        if (enabled) {
            button.removeAttribute('disabled');
        } else {
            button.setAttribute('disabled', 'true');
        }
    }
}
