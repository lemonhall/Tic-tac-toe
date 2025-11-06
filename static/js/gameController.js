// Game Controller - 主控制器，协调各个模块
import { ApiClient } from './api.js';
import { GameStateManager } from './gameState.js';
import { UIManager } from './ui.js';
import { EventHandler } from './events.js';

export class GameController {
    constructor() {
        this.api = new ApiClient();
        this.state = new GameStateManager();
        this.ui = new UIManager();
        this.events = new EventHandler(this);
        
        this.currentMode = 'human-vs-human';
        this.aiMoveInProgress = false;
    }

    // 初始化游戏控制器
    async init() {
        console.log('初始化井字棋决斗场...');
        this.events.init();
        this.ui.showMessage('选择游戏模式并点击"开始游戏"', 'info');
        console.log('初始化完成！');
    }

    // 设置游戏模式
    setGameMode(mode) {
        this.currentMode = mode;
        this.ui.setActiveMode(mode);
        
        // 根据模式自动设置玩家类型
        switch(mode) {
            case 'human-vs-human':
                this.ui.setPlayerTypes('human', 'human');
                this.state.setSpectatorMode(false);
                break;
            case 'human-vs-ai':
                this.ui.setPlayerTypes('human', 'ai');
                this.state.setSpectatorMode(false);
                break;
            case 'ai-vs-ai':
                this.ui.setPlayerTypes('ai', 'ai');
                this.state.setSpectatorMode(false);
                break;
            case 'spectator':
                this.ui.setPlayerTypes('ai', 'ai');
                this.state.setSpectatorMode(true);
                break;
        }
        
        this.ui.showMessage(`已选择: ${this.getModeName(mode)}`, 'info');
    }

    // 获取模式名称
    getModeName(mode) {
        const names = {
            'human-vs-human': '人类 vs 人类',
            'human-vs-ai': '人类 vs AI',
            'ai-vs-ai': 'AI vs AI',
            'spectator': '观战模式'
        };
        return names[mode] || mode;
    }

    // 开始游戏
    async startGame() {
        try {
            this.ui.showMessage('正在创建游戏...', 'info');
            this.ui.updateConnectionStatus('connecting');
            
            const playerTypes = this.ui.getPlayerTypes();
            
            // 创建游戏
            const response = await this.api.createGame(playerTypes.playerX, playerTypes.playerO);
            
            if (response.status === 'success') {
                this.state.initGame(response.game_id, playerTypes.playerX, playerTypes.playerO);
                this.state.updateFromServer(response.game_state);
                
                // 连接SSE
                this.connectToGameEvents(response.game_id);
                
                // 更新UI
                this.ui.renderBoard(this.state.board);
                this.ui.updateGameInfo(response.game_id, this.state.currentPlayer, this.state.gameStatus);
                this.ui.updateCurrentPlayer(this.state.currentPlayer, this.state.getCurrentPlayerType());
                this.ui.clearMoveHistory();
                this.ui.hideWinningLine();
                this.ui.setBoardEnabled(true);
                
                this.ui.showMessage('游戏开始！', 'success');
                
                // 如果第一个玩家是AI，触发AI移动
                if (this.state.shouldRequestAIMove()) {
                    await this.requestAIMove();
                }
            } else {
                this.ui.showMessage('创建游戏失败: ' + response.message, 'error');
            }
        } catch (error) {
            console.error('开始游戏失败:', error);
            this.ui.showMessage('开始游戏失败: ' + error.message, 'error');
            this.ui.updateConnectionStatus('disconnected');
        }
    }

    // 重置游戏
    async resetGame() {
        try {
            if (!this.state.gameId) {
                this.ui.showMessage('请先开始游戏', 'warning');
                return;
            }
            
            this.ui.showMessage('正在重置游戏...', 'info');
            
            const response = await this.api.resetGame(this.state.gameId);
            
            if (response.status === 'success') {
                this.state.updateFromServer(response.game_state);
                
                this.ui.renderBoard(this.state.board);
                this.ui.updateGameInfo(this.state.gameId, this.state.currentPlayer, this.state.gameStatus);
                this.ui.updateCurrentPlayer(this.state.currentPlayer, this.state.getCurrentPlayerType());
                this.ui.clearMoveHistory();
                this.ui.hideWinningLine();
                this.ui.setBoardEnabled(true);
                
                this.ui.showMessage('游戏已重置', 'success');
                
                // 如果第一个玩家是AI，触发AI移动
                if (this.state.shouldRequestAIMove()) {
                    await this.requestAIMove();
                }
            } else {
                this.ui.showMessage('重置游戏失败: ' + response.message, 'error');
            }
        } catch (error) {
            console.error('重置游戏失败:', error);
            this.ui.showMessage('重置游戏失败: ' + error.message, 'error');
        }
    }

    // 暂停游戏
    pauseGame() {
        // TODO: 实现暂停功能
        this.ui.showMessage('暂停功能待实现', 'warning');
    }

    // 处理格子点击
    async handleCellClick(row, col) {
        if (!this.state.canMakeMove(row, col)) {
            if (this.state.isSpectator) {
                this.ui.showMessage('观战模式下不能下棋', 'warning');
            } else if (this.state.getCurrentPlayerType() !== 'human') {
                this.ui.showMessage('当前是AI回合，请等待', 'warning');
            }
            return;
        }
        
        try {
            this.ui.showMessage('正在下棋...', 'info');
            
            const response = await this.api.makeMove(this.state.gameId, row, col);
            
            if (response.status === 'success') {
                // 更新会通过SSE事件处理
                console.log('下棋成功');
            } else {
                this.ui.showMessage('下棋失败: ' + response.message, 'error');
            }
        } catch (error) {
            console.error('下棋失败:', error);
            this.ui.showMessage('下棋失败: ' + error.message, 'error');
        }
    }

    // 请求AI移动
    async requestAIMove() {
        if (this.aiMoveInProgress) {
            return;
        }
        
        this.aiMoveInProgress = true;
        
        try {
            console.log('请求AI移动...');
            this.ui.showMessage('AI正在思考...', 'info');
            
            const response = await this.api.requestAIMove(this.state.gameId);
            
            if (response.status === 'success') {
                console.log('AI移动成功');
            } else {
                console.error('AI移动失败:', response.message);
                this.ui.showMessage('AI移动失败: ' + response.message, 'error');
            }
        } catch (error) {
            console.error('请求AI移动失败:', error);
            this.ui.showMessage('请求AI移动失败: ' + error.message, 'error');
        } finally {
            this.aiMoveInProgress = false;
        }
    }

    // 更新玩家类型
    updatePlayerType(player, type) {
        if (player === 'X') {
            this.state.playerXType = type;
        } else {
            this.state.playerOType = type;
        }
    }

    // 连接游戏事件流
    connectToGameEvents(gameId) {
        this.api.connectEventStream(
            gameId,
            (data) => this.handleGameEvent(data),
            (error) => {
                console.error('SSE错误:', error);
                this.ui.updateConnectionStatus('disconnected');
                this.ui.showMessage('连接断开，请刷新页面', 'error');
            },
            () => {
                this.ui.updateConnectionStatus('connected');
            }
        );
    }

    // 处理游戏事件
    async handleGameEvent(data) {
        console.log('收到游戏事件:', data);
        
        switch(data.type) {
            case 'move':
                await this.handleMoveEvent(data);
                break;
            case 'game_over':
                this.handleGameOverEvent(data);
                break;
            case 'reset':
                this.handleResetEvent(data);
                break;
            case 'state_update':
                this.handleStateUpdateEvent(data);
                break;
            default:
                console.log('未知事件类型:', data.type);
        }
    }

    // 处理移动事件
    async handleMoveEvent(data) {
        const { row, col, player, move_number } = data;
        
        // 更新状态
        this.state.board[row][col] = player;
        this.state.addMove(player, row, col, move_number);
        
        // 更新UI
        this.ui.updateCell(row, col, player);
        this.ui.addMoveToHistory({ player, row, col, moveNumber: move_number });
        
        // 更新当前玩家
        if (data.next_player) {
            this.state.currentPlayer = data.next_player;
            this.ui.updateCurrentPlayer(data.next_player, this.state.getCurrentPlayerType());
        }
        
        this.ui.updateGameInfo(this.state.gameId, this.state.currentPlayer, this.state.gameStatus);
        this.ui.showMessage(`玩家 ${player} 在 (${row}, ${col}) 下棋`, 'info');
        
        // 如果下一个玩家是AI，触发AI移动
        if (this.state.shouldRequestAIMove()) {
            // 延迟一下，让玩家看到上一步
            setTimeout(() => {
                this.requestAIMove();
            }, 500);
        }
    }

    // 处理游戏结束事件
    handleGameOverEvent(data) {
        const { winner, winning_line, is_draw } = data;
        
        this.state.gameStatus = 'finished';
        this.state.winner = winner;
        this.state.winningLine = winning_line;
        
        // 更新统计
        this.state.updateStats();
        this.ui.updateStats(this.state.stats);
        
        // 显示获胜线条
        if (winning_line) {
            this.ui.showWinningLine(winning_line);
        }
        
        // 更新UI
        this.ui.setBoardEnabled(false);
        this.ui.updateGameInfo(this.state.gameId, '-', this.state.gameStatus);
        
        if (is_draw) {
            this.ui.showMessage('游戏结束 - 平局！', 'info');
            this.ui.showGameOverModal(null, true);
        } else {
            this.ui.showMessage(`游戏结束 - 玩家 ${winner} 获胜！`, 'success');
            this.ui.showGameOverModal(winner, false);
        }
    }

    // 处理重置事件
    handleResetEvent(data) {
        this.state.updateFromServer(data.game_state);
        
        this.ui.renderBoard(this.state.board);
        this.ui.updateGameInfo(this.state.gameId, this.state.currentPlayer, this.state.gameStatus);
        this.ui.updateCurrentPlayer(this.state.currentPlayer, this.state.getCurrentPlayerType());
        this.ui.clearMoveHistory();
        this.ui.hideWinningLine();
        this.ui.setBoardEnabled(true);
        
        this.ui.showMessage('游戏已重置', 'success');
    }

    // 处理状态更新事件
    handleStateUpdateEvent(data) {
        this.state.updateFromServer(data.game_state);
        
        this.ui.renderBoard(this.state.board);
        this.ui.updateGameInfo(this.state.gameId, this.state.currentPlayer, this.state.gameStatus);
        this.ui.updateCurrentPlayer(this.state.currentPlayer, this.state.getCurrentPlayerType());
    }
}
