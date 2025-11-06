// Main Entry Point - 应用入口
import { GameController } from './gameController.js';

// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', async () => {
    console.log('井字棋决斗场 - 启动中...');
    
    try {
        // 创建游戏控制器
        const gameController = new GameController();
        
        // 初始化
        await gameController.init();
        
        // 将控制器暴露到全局，方便调试
        window.gameController = gameController;
        
        console.log('✓ 系统就绪！');
    } catch (error) {
        console.error('初始化失败:', error);
        alert('系统初始化失败: ' + error.message);
    }
});

// 全局错误处理
window.addEventListener('error', (event) => {
    console.error('全局错误:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('未处理的Promise拒绝:', event.reason);
});
