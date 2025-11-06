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
        this.autoSpectateActive = false;  // 自动观战标记
        this.autoSpectateTimer = null;    // 自动观战定时器
        this.timelineReplayTimers = [];   // 保存当前replay用的所有定时器，便于清理
        this.activeTimelineGameId = null; // 当前使用timeline-stream观战的游戏ID
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

    // 观战游戏
    async spectateGame() {
        try {
            this.ui.showMessage('正在获取进行中的游戏...', 'info');
            
            const games = await this.api.getGamesList('in_progress');
            
            if (Object.keys(games).length === 0) {
                this.ui.showMessage('当前没有进行中的游戏', 'warning');
                return;
            }
            
            const gameEntries = Object.entries(games);
            
            // 如果只有一个游戏，自动加入
            if (gameEntries.length === 1) {
                const [gameId] = gameEntries[0];
                await this.joinSpectatorGame(gameId);
            } else {
                // 如果有多个游戏，显示列表让用户选择
                this.showGameListModal(gameEntries);
            }
        } catch (error) {
            console.error('观战游戏失败:', error);
            this.ui.showMessage('观战游戏失败: ' + error.message, 'error');
        }
    }

    // 加入观战游戏
    async joinSpectatorGame(gameId) {
        try {
            this.ui.showMessage('正在加入游戏...', 'info');
            
            // 获取游戏状态
            const response = await this.api.getGameState(gameId);
            
            if (response.status === 'success') {
                const gameState = response.game_state;
                
                // 初始化为观战模式
                this.state.initGame(gameId, gameState.player_x_type, gameState.player_o_type);
                this.state.updateFromServer(gameState);
                this.state.setSpectatorMode(true);
                
                // 如果是自动观战模式，使用 timeline-stream（阻塞到结束一次性推送）
                if (this.autoSpectateActive) {
                    const replaySpeed = this.getReplaySpeed();
                    console.log(`[autoSpectate] 使用 timeline-stream 观战游戏 ${gameId}, replaySpeed=${replaySpeed}`);
                    this.startTimelineReplay(gameId, replaySpeed);
                } else {
                    // 普通手动观战，实时事件流
                    this.connectToGameEvents(gameId);
                }
                
                // 更新UI
                this.ui.renderBoard(this.state.board);
                this.ui.updateGameInfo(gameId, this.state.currentPlayer, this.state.gameStatus);
                this.ui.updateCurrentPlayer(this.state.currentPlayer, this.state.getCurrentPlayerType());
                this.ui.clearMoveHistory();
                this.ui.hideWinningLine();
                this.ui.setBoardEnabled(false);  // 观战模式禁用棋盘
                this.ui.setActiveMode('spectator');
                
                this.ui.showMessage('已加入观战，游戏ID: ' + gameId, 'success');
            } else {
                this.ui.showMessage('获取游戏状态失败', 'error');
            }
        } catch (error) {
            console.error('加入观战游戏失败:', error);
            this.ui.showMessage('加入观战游戏失败: ' + error.message, 'error');
        }
    }

    // 显示游戏列表模态框
    showGameListModal(games) {
        // 创建模态框容器
        const modalId = 'game-list-modal';
        let modal = document.getElementById(modalId);
        
        if (!modal) {
            modal = document.createElement('div');
            modal.id = modalId;
            modal.className = 'modal';
            document.body.appendChild(modal);
        }
        
        // 生成游戏列表HTML
        const gameListHTML = games.map(([gameId, game], index) => {
            const status = `${game.player_x_type} vs ${game.player_o_type}`;
            const moves = game.move_count || 0;
            const displayId = gameId.substring(0, 8) + '...';
            
            return `
                <div class="game-item" data-game-id="${gameId}">
                    <div class="game-info">
                        <div class="game-id">${displayId}</div>
                        <div class="game-details">${status} • ${moves}步</div>
                    </div>
                    <button class="game-select-btn" data-game-id="${gameId}">观战</button>
                </div>
            `;
        }).join('');
        
        // 设置模态框内容
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>选择观战的游戏</h2>
                </div>
                <div class="modal-body" style="padding: 0;">
                    <div class="game-list">
                        ${gameListHTML}
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="modal-btn secondary" id="cancel-spectate">取消</button>
                </div>
            </div>
        `;
        
        // 显示模态框
        modal.classList.add('show');
        
        // 为所有"观战"按钮添加事件监听
        modal.querySelectorAll('.game-select-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const gameId = e.target.getAttribute('data-game-id');
                modal.classList.remove('show');
                this.joinSpectatorGame(gameId);
            });
        });
        
        // 为"取消"按钮添加事件监听
        modal.querySelector('#cancel-spectate').addEventListener('click', () => {
            modal.classList.remove('show');
            this.ui.showMessage('已取消观战', 'info');
        });
        
        // 点击背景关闭模态框
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('show');
                this.ui.showMessage('已取消观战', 'info');
            }
        });
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
            case 'game_created':
                // 游戏创建事件 - 通常在连接时发送，可以忽略
                console.log('✓ 游戏已创建:', data.game_id);
                break;
            case 'game_deleted':
                // 游戏被删除事件 - 游戏已过期或被清理
                console.warn('⚠️  游戏已被删除（可能是超时）');
                this.ui.showMessage('游戏已超时或被清理', 'error');
                this.api.closeEventStream();
                break;
            default:
                console.warn('⚠️  未知事件类型:', data.type);
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
            this.ui.showGameOverModal(null, true, this.autoSpectateActive);
        } else {
            this.ui.showMessage(`游戏结束 - 玩家 ${winner} 获胜！`, 'success');
            this.ui.showGameOverModal(winner, false, this.autoSpectateActive);
        }
        
        // 如果处于自动观战模式，延迟后自动查找下一个活跃棋局
        if (this.autoSpectateActive) {
            console.log('🔄 自动观战模式：等待下一个活跃棋局...');
            this.ui.showMessage('⏳ 正在查找下一个棋局...', 'info');
            
            // 清除之前的定时器
            if (this.autoSpectateTimer) {
                clearTimeout(this.autoSpectateTimer);
            }
            
            // 2秒后开始查找
            this.autoSpectateTimer = setTimeout(() => {
                this.findAndJoinNextGame();
            }, 2000);
        }
    }
    
    // 启动自动观战
    async startAutoSpectate() {
        console.log('🎬 启动自动观战模式 (全局时间线)');
        this.autoSpectateActive = true;
        this.ui.showMessage('� 已连接全局时间线流，等待棋局完成...', 'info');
        // 连接全局 timelines 流，按完成顺序接收每局
        const replaySpeed = this.getReplaySpeed();
        this.pendingTimelines = [];
        this.replaying = false;
        this.api.connectGlobalTimelines(
            replaySpeed,
            (data) => {
                // data: {type:'timeline', game_id, timeline}
                const { game_id, timeline } = data;
                console.log(`[global-timeline] 收到已结束棋局 ${game_id}, moves=${timeline.moves.length}`);
                // 若正在回放，排队
                if (this.replaying) {
                    this.pendingTimelines.push(data);
                } else {
                    this.playTimelineData(data);
                }
            },
            (err) => {
                console.error('global timelines 连接错误:', err);
                this.ui.showMessage('全局时间线连接错误: ' + err.message, 'error');
            },
            () => {
                console.log('[global-timelines] open');
            }
        );
    }
    
    // 停止自动观战
    stopAutoSpectate() {
        console.log('⏹️ 停止自动观战模式');
        this.autoSpectateActive = false;
        
        if (this.autoSpectateTimer) {
            clearTimeout(this.autoSpectateTimer);
            this.autoSpectateTimer = null;
        }
        
        this.ui.showMessage('已停止自动观战', 'info');
    }
    
    // 查找并加入下一个活跃棋局
    async findAndJoinNextGame() {
        try {
            console.log('🔍 查找活跃棋局...');
            
            const games = await this.api.getGamesList('in_progress');
            const gameIds = Object.keys(games);
            
            if (gameIds.length === 0) {
                console.log('⏳ 暂无活跃棋局，继续等待...');
                this.ui.showMessage('⏳ 等待新棋局...', 'info');
                
                // 继续轮询，5秒后再查找
                if (this.autoSpectateActive) {
                    this.autoSpectateTimer = setTimeout(() => {
                        this.findAndJoinNextGame();
                    }, 5000);
                }
            } else {
                // 获取第一个活跃棋局
                const gameId = gameIds[0];
                console.log(`📍 发现棋局: ${gameId}`);
                
                // 加入观战
                await this.joinSpectatorGame(gameId);
            }
        } catch (error) {
            console.error('❌ 查找棋局失败:', error);
            this.ui.showMessage('查找棋局失败: ' + error.message, 'error');
            
            // 继续轮询
            if (this.autoSpectateActive) {
                this.autoSpectateTimer = setTimeout(() => {
                    this.findAndJoinNextGame();
                }, 5000);
            }
        }
    }

    // ===== Timeline Replay 功能 =====
    // 获取当前UI选择的replay速度，若未提供则默认1.0
    getReplaySpeed() {
        const select = document.getElementById('replay-speed');
        if (!select) return 2.0; // 默认2.0倍速
        const val = parseFloat(select.value);
        return isNaN(val) ? 2.0 : val;
    }

    // 开始使用 timeline-stream 观战某个游戏（阻塞到结束后一次性获取全量时间线）
    startTimelineReplay(gameId, replaySpeed = 1.0) {
        // 清理旧的定时器
        this.clearTimelineReplayTimers();
        this.activeTimelineGameId = gameId;
        this.ui.showMessage(`⌛ 正在等待棋局结束以获取时间线...`, 'info');
        this.api.connectTimelineStream(
            gameId,
            replaySpeed,
            (timeline) => this.handleTimelineReplay(timeline, replaySpeed),
            (err) => {
                console.error('timeline-stream 错误:', err);
                this.ui.showMessage('时间线连接错误: ' + err.message, 'error');
            },
            () => {
                console.log('[timeline-stream] open');
            }
        );
    }

    // 处理时间线（整局回放）
    handleTimelineReplay(timeline, replaySpeed = 1.0) {
        console.log('[timeline] 收到整局时间线:', timeline);
        const moves = timeline.moves || [];
        if (!moves.length) {
            this.ui.showMessage('该棋局没有任何落子', 'warning');
            return;
        }

        // 重置界面用于回放
        this.ui.clearMoveHistory();
        this.ui.hideWinningLine();
        // 清空棋盘显示
        for (let r = 0; r < this.state.board.length; r++) {
            for (let c = 0; c < this.state.board[r].length; c++) {
                this.state.board[r][c] = null;
                this.ui.updateCell(r, c, '');
            }
        }
        this.state.moveHistory = [];
        this.state.gameStatus = 'replay';
        this.state.winner = null;
        this.state.winningLine = null;
        this.ui.updateGameInfo(this.activeTimelineGameId, '-', 'replay');
        this.ui.showMessage('▶️ 开始回放棋局...', 'success');

        const startedAt = timeline.started_at ? Date.parse(timeline.started_at) : null;
        // 如果没有 started_at 或 timestamp 差值，则均匀播放
        let uniformInterval = 800; // ms 默认每步间隔

        moves.forEach((mv, idx) => {
            let delay;
            if (startedAt && mv.timestamp) {
                const mvTs = Date.parse(mv.timestamp);
                delay = Math.max(0, mvTs - startedAt);
            } else {
                delay = idx * uniformInterval; // 均匀
            }
            // 应用速度因子
            delay = delay / Math.max(replaySpeed, 0.01);

            const timer = setTimeout(() => {
                // 更新内部状态
                this.state.board[mv.row][mv.col] = mv.player;
                this.state.addMove(mv.player, mv.row, mv.col, mv.move_number);
                // 更新UI
                this.ui.updateCell(mv.row, mv.col, mv.player);
                this.ui.addMoveToHistory({ player: mv.player, row: mv.row, col: mv.col, moveNumber: mv.move_number });
                this.ui.updateGameInfo(this.activeTimelineGameId, mv.player, 'replay');
                if (idx === moves.length - 1) {
                    // 最后一手，显示结果
                    this.state.gameStatus = 'finished';
                    this.state.winner = timeline.winner || null;
                    if (timeline.winning_line) {
                        this.state.winningLine = timeline.winning_line;
                        this.ui.showWinningLine(timeline.winning_line);
                    }
                    if (timeline.is_draw) {
                        this.ui.showMessage('回放结束 - 平局', 'info');
                    } else if (timeline.winner) {
                        this.ui.showMessage(`回放结束 - 玩家 ${timeline.winner} 获胜`, 'success');
                    } else {
                        this.ui.showMessage('回放结束', 'info');
                    }
                    // 回放结束后更新统计（观战模式的累计胜负）
                    this.state.updateStats();
                    this.ui.updateStats(this.state.stats);
                    // 回放结束，检查队列
                    this.replaying = false;
                    if (this.pendingTimelines && this.pendingTimelines.length) {
                        const next = this.pendingTimelines.shift();
                        setTimeout(() => this.playTimelineData(next), 800);
                    }
                }
            }, delay);
            this.timelineReplayTimers.push(timer);
        });
        this.replaying = true;
    }

    clearTimelineReplayTimers() {
        if (this.timelineReplayTimers.length) {
            this.timelineReplayTimers.forEach(t => clearTimeout(t));
            this.timelineReplayTimers = [];
        }
    }

    // 供全局timeline数据入口调用
    playTimelineData(data) {
        const { game_id, timeline } = data;
        this.activeTimelineGameId = game_id;
        this.handleTimelineReplay(timeline, timeline.replay_speed || this.getReplaySpeed());
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
