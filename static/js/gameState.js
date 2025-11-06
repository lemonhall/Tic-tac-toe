// Game State Manager - 管理游戏状态
export class GameStateManager {
    constructor() {
        this.gameId = null;
        this.board = Array(3).fill(null).map(() => Array(3).fill(null));
        this.currentPlayer = 'X';
        this.gameStatus = 'not_started'; // not_started, in_progress, finished
        this.winner = null;
        this.winningLine = null;
        this.playerXType = 'human';
        this.playerOType = 'human';
        this.moveHistory = [];
        this.isSpectator = false;
        this.stats = {
            xWins: 0,
            oWins: 0,
            draws: 0
        };
    }

    // 初始化新游戏
    initGame(gameId, playerXType, playerOType) {
        this.gameId = gameId;
        this.playerXType = playerXType;
        this.playerOType = playerOType;
        this.resetBoard();
    }

    // 重置棋盘
    resetBoard() {
        this.board = Array(3).fill(null).map(() => Array(3).fill(null));
        this.currentPlayer = 'X';
        this.gameStatus = 'in_progress';
        this.winner = null;
        this.winningLine = null;
        this.moveHistory = [];
    }

    // 更新游戏状态（从服务器）
    updateFromServer(serverState) {
        this.board = serverState.board;
        this.currentPlayer = serverState.current_player;
        this.gameStatus = serverState.status;
        this.winner = serverState.winner;
        this.winningLine = serverState.winning_line;
        
        if (serverState.game_id) {
            this.gameId = serverState.game_id;
        }
    }

    // 添加移动到历史
    addMove(player, row, col, moveNumber) {
        this.moveHistory.push({
            player,
            row,
            col,
            moveNumber,
            timestamp: new Date()
        });
    }

    // 检查是否可以下棋
    canMakeMove(row, col) {
        if (this.gameStatus !== 'in_progress') {
            return false;
        }
        if (this.board[row][col] !== null) {
            return false;
        }
        
        // 检查当前玩家类型
        const currentPlayerType = this.currentPlayer === 'X' ? this.playerXType : this.playerOType;
        
        // 如果是观战模式，不能下棋
        if (this.isSpectator) {
            return false;
        }
        
        // 如果当前玩家是AI或外部Agent，人类不能下棋
        if (currentPlayerType !== 'human') {
            return false;
        }
        
        return true;
    }

    // 获取当前玩家类型
    getCurrentPlayerType() {
        return this.currentPlayer === 'X' ? this.playerXType : this.playerOType;
    }

    // 是否需要AI移动
    shouldRequestAIMove() {
        const currentPlayerType = this.getCurrentPlayerType();
        return this.gameStatus === 'in_progress' && currentPlayerType === 'ai';
    }

    // 更新统计数据
    updateStats() {
        if (this.winner === 'X') {
            this.stats.xWins++;
        } else if (this.winner === 'O') {
            this.stats.oWins++;
        } else if (this.gameStatus === 'finished' && this.winner === null) {
            this.stats.draws++;
        }
    }

    // 设置观战模式
    setSpectatorMode(isSpectator) {
        this.isSpectator = isSpectator;
    }

    // 获取棋盘的字符串表示（用于调试）
    getBoardString() {
        return this.board.map(row => 
            row.map(cell => cell || '-').join(' ')
        ).join('\n');
    }
}
