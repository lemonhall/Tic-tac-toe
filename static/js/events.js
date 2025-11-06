// Event Handler - 处理用户交互事件
export class EventHandler {
    constructor(gameController) {
        this.controller = gameController;
        this.ui = gameController.ui;
    }

    // 初始化所有事件监听器
    init() {
        this.setupBoardEvents();
        this.setupControlEvents();
        this.setupModeEvents();
        this.setupModalEvents();
    }

    // 设置棋盘点击事件
    setupBoardEvents() {
        this.ui.elements.cells.forEach(cell => {
            cell.addEventListener('click', async (e) => {
                const row = parseInt(cell.dataset.row);
                const col = parseInt(cell.dataset.col);
                await this.controller.handleCellClick(row, col);
            });
        });
    }

    // 设置控制按钮事件
    setupControlEvents() {
        // 开始游戏
        this.ui.elements.startBtn.addEventListener('click', async () => {
            await this.controller.startGame();
        });

        // 重置游戏
        this.ui.elements.resetBtn.addEventListener('click', async () => {
            await this.controller.resetGame();
        });

        // 暂停游戏
        this.ui.elements.pauseBtn.addEventListener('click', () => {
            this.controller.pauseGame();
        });

        // 玩家类型变化
        this.ui.elements.playerXSelect.addEventListener('change', (e) => {
            this.controller.updatePlayerType('X', e.target.value);
        });

        this.ui.elements.playerOSelect.addEventListener('change', (e) => {
            this.controller.updatePlayerType('O', e.target.value);
        });
    }

    // 设置模式选择事件
    setupModeEvents() {
        this.ui.elements.modeBtns.forEach(btn => {
            btn.addEventListener('click', async () => {
                const mode = btn.dataset.mode;
                
                // 如果选择观战模式，启动自动观战
                if (mode === 'spectator') {
                    await this.controller.startAutoSpectate();
                } else {
                    this.controller.setGameMode(mode);
                }
            });
        });
    }

    // 设置模态框事件
    setupModalEvents() {
        // 新游戏按钮
        this.ui.elements.modalNewGame.addEventListener('click', async () => {
            this.ui.hideGameOverModal();
            await this.controller.startGame();
        });

        // 关闭按钮
        this.ui.elements.modalClose.addEventListener('click', () => {
            this.ui.hideGameOverModal();
        });

        // 点击背景关闭
        this.ui.elements.modal.addEventListener('click', (e) => {
            if (e.target === this.ui.elements.modal) {
                this.ui.hideGameOverModal();
            }
        });
    }
}
