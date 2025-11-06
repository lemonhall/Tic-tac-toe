// API Client - 处理所有后端API通信
export class ApiClient {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
        this.eventSource = null;
    }

    // 创建新游戏
    async createGame(playerXType, playerOType) {
        const response = await fetch(`${this.baseUrl}/api/game/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                player_x_type: playerXType,
                player_o_type: playerOType
            })
        });
        return await response.json();
    }

    // 获取游戏状态
    async getGameState(gameId) {
        const response = await fetch(`${this.baseUrl}/api/game/${gameId}/state`);
        return await response.json();
    }

    // 下棋
    async makeMove(gameId, row, col, playerId = null) {
        const response = await fetch(`${this.baseUrl}/api/game/${gameId}/move`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                row,
                col,
                player_id: playerId
            })
        });
        return await response.json();
    }

    // 重置游戏
    async resetGame(gameId) {
        const response = await fetch(`${this.baseUrl}/api/game/${gameId}/reset`, {
            method: 'POST'
        });
        return await response.json();
    }

    // AI移动
    async requestAIMove(gameId) {
        const response = await fetch(`${this.baseUrl}/api/game/${gameId}/ai-move`, {
            method: 'POST'
        });
        return await response.json();
    }

    // 获取所有游戏列表
    async getGamesList(statusFilter = 'in_progress') {
        try {
            const url = statusFilter 
                ? `${this.baseUrl}/api/games?status=${statusFilter}`
                : `${this.baseUrl}/api/games`;
            
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            return data.games || {};
        } catch (error) {
            console.error('获取游戏列表失败:', error);
            return {};
        }
    }

    // 连接SSE事件流
    connectEventStream(gameId, onMessage, onError, onOpen) {
        if (this.eventSource) {
            this.eventSource.close();
        }

        this.eventSource = new EventSource(`${this.baseUrl}/api/game/${gameId}/events`);

        this.eventSource.onopen = () => {
            console.log('SSE连接已建立');
            if (onOpen) onOpen();
        };

        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (onMessage) onMessage(data);
            } catch (e) {
                console.error('解析SSE消息失败:', e);
            }
        };

        this.eventSource.onerror = (error) => {
            console.error('SSE连接错误:', error);
            if (onError) onError(error);
        };

        return this.eventSource;
    }

    // 关闭SSE连接
    closeEventStream() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }
}
