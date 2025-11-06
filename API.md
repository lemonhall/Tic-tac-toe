# API 文档

## 概述

井字棋决斗场提供了完整的RESTful API和SSE事件流，支持所有游戏操作。

## 基础信息

- **基础URL**: `http://localhost:5000`
- **内容类型**: `application/json`
- **事件流**: Server-Sent Events (SSE)

---

## API端点

### 1. 健康检查

检查服务器状态。

**端点**: `GET /api/health`

**响应**:
```json
{
  "status": "healthy",
  "service": "Tic-Tac-Toe Arena",
  "version": "1.0.0",
  "active_games": 2
}
```

---

### 2. 创建游戏

创建一个新的井字棋游戏。

**端点**: `POST /api/game/create`

**请求体**:
```json
{
  "player_x_type": "human",
  "player_o_type": "ai"
}
```

**参数说明**:
- `player_x_type`: 玩家X的类型 (`human` | `ai` | `agent`)
- `player_o_type`: 玩家O的类型 (`human` | `ai` | `agent`)

**响应**:
```json
{
  "status": "success",
  "message": "游戏创建成功",
  "game_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "game_state": {
    "game_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "board": [[null, null, null], [null, null, null], [null, null, null]],
    "current_player": "X",
    "status": "in_progress",
    "winner": null,
    "winning_line": null,
    "move_count": 0,
    "move_history": [],
    "player_x_type": "human",
    "player_o_type": "ai",
    "created_at": "2025-11-06T10:30:00",
    "updated_at": "2025-11-06T10:30:00"
  }
}
```

---

### 3. 获取游戏状态

获取指定游戏的当前状态。

**端点**: `GET /api/game/{game_id}/state`

**路径参数**:
- `game_id`: 游戏ID

**响应**:
```json
{
  "status": "success",
  "game_state": {
    "game_id": "...",
    "board": [...],
    "current_player": "X",
    "status": "in_progress",
    ...
  }
}
```

---

### 4. 下棋

在指定位置放置标记。

**端点**: `POST /api/game/{game_id}/move`

**路径参数**:
- `game_id`: 游戏ID

**请求体**:
```json
{
  "row": 0,
  "col": 1,
  "player_id": null
}
```

**参数说明**:
- `row`: 行号 (0-2)
- `col`: 列号 (0-2)
- `player_id`: 可选，玩家标识

**响应 - 成功**:
```json
{
  "status": "success",
  "message": "移动成功",
  "result": {
    "success": true,
    "game_over": false,
    "next_player": "O"
  },
  "game_state": {...}
}
```

**响应 - 游戏结束**:
```json
{
  "status": "success",
  "message": "移动成功",
  "result": {
    "success": true,
    "game_over": true,
    "winner": "X",
    "winning_line": [[0, 0], [0, 2]],
    "is_draw": false
  },
  "game_state": {...}
}
```

**响应 - 错误**:
```json
{
  "status": "error",
  "message": "非法移动"
}
```

---

### 5. AI移动

请求AI进行移动。

**端点**: `POST /api/game/{game_id}/ai-move`

**路径参数**:
- `game_id`: 游戏ID

**响应**:
```json
{
  "status": "success",
  "message": "移动成功",
  "result": {...},
  "game_state": {...}
}
```

---

### 6. 重置游戏

重置游戏到初始状态。

**端点**: `POST /api/game/{game_id}/reset`

**路径参数**:
- `game_id`: 游戏ID

**响应**:
```json
{
  "status": "success",
  "message": "游戏已重置",
  "game_state": {...}
}
```

---

### 7. 列出所有游戏

获取所有活动游戏的列表。

**端点**: `GET /api/games`

**响应**:
```json
{
  "status": "success",
  "games": {
    "game-id-1": {...},
    "game-id-2": {...}
  },
  "count": 2
}
```

---

### 8. 删除游戏

删除指定的游戏。

**端点**: `DELETE /api/game/{game_id}`

**路径参数**:
- `game_id`: 游戏ID

**响应**:
```json
{
  "status": "success",
  "message": "游戏已删除"
}
```

---

## SSE 事件流

### 连接事件流

**端点**: `GET /api/game/{game_id}/events`

**路径参数**:
- `game_id`: 游戏ID

**使用方法** (JavaScript):
```javascript
const eventSource = new EventSource(`/api/game/${gameId}/events`);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('收到事件:', data);
};

eventSource.onerror = (error) => {
  console.error('SSE错误:', error);
};
```

---

### 事件类型

#### 1. connected - 连接建立
```json
{
  "type": "connected",
  "game_id": "..."
}
```

#### 2. state_update - 状态更新
```json
{
  "type": "state_update",
  "game_state": {...}
}
```

#### 3. move - 玩家移动
```json
{
  "type": "move",
  "game_id": "...",
  "row": 0,
  "col": 1,
  "player": "X",
  "move_number": 1,
  "next_player": "O"
}
```

#### 4. game_over - 游戏结束
```json
{
  "type": "game_over",
  "game_id": "...",
  "winner": "X",
  "winning_line": [[0, 0], [0, 2]],
  "is_draw": false
}
```

#### 5. reset - 游戏重置
```json
{
  "type": "reset",
  "game_id": "...",
  "game_state": {...}
}
```

#### 6. error - 错误
```json
{
  "type": "error",
  "message": "错误描述"
}
```

---

## 游戏状态对象

```json
{
  "game_id": "uuid",
  "board": [
    ["X", null, "O"],
    [null, "X", null],
    [null, null, null]
  ],
  "current_player": "X",
  "status": "in_progress",
  "winner": null,
  "winning_line": null,
  "move_count": 3,
  "move_history": [
    {
      "player": "X",
      "row": 0,
      "col": 0,
      "move_number": 1,
      "timestamp": "2025-11-06T10:30:01"
    }
  ],
  "player_x_type": "human",
  "player_o_type": "ai",
  "created_at": "2025-11-06T10:30:00",
  "updated_at": "2025-11-06T10:30:05"
}
```

**字段说明**:
- `game_id`: 游戏唯一标识
- `board`: 3x3棋盘，`null`表示空格
- `current_player`: 当前玩家 (`X` | `O`)
- `status`: 游戏状态 (`not_started` | `in_progress` | `finished`)
- `winner`: 获胜玩家 (`X` | `O` | `null`)
- `winning_line`: 获胜连线坐标 `[[row1, col1], [row2, col2]]`
- `move_count`: 移动次数
- `move_history`: 移动历史记录
- `player_x_type`: 玩家X类型
- `player_o_type`: 玩家O类型
- `created_at`: 创建时间
- `updated_at`: 更新时间

---

## 错误码

| HTTP状态码 | 说明 |
|-----------|------|
| 200 | 成功 |
| 400 | 请求错误（参数错误、非法移动等） |
| 404 | 资源不存在（游戏不存在） |
| 500 | 服务器内部错误 |

---

## 使用示例

### Python示例

```python
import requests
import json

# 创建游戏
response = requests.post('http://localhost:5000/api/game/create', 
    json={'player_x_type': 'human', 'player_o_type': 'ai'})
game = response.json()
game_id = game['game_id']

# 下棋
response = requests.post(f'http://localhost:5000/api/game/{game_id}/move',
    json={'row': 0, 'col': 0})
result = response.json()

# 获取状态
response = requests.get(f'http://localhost:5000/api/game/{game_id}/state')
state = response.json()
```

### JavaScript示例

```javascript
// 创建游戏
const response = await fetch('/api/game/create', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    player_x_type: 'human',
    player_o_type: 'ai'
  })
});
const game = await response.json();

// 连接SSE
const eventSource = new EventSource(`/api/game/${game.game_id}/events`);
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  handleGameEvent(data);
};

// 下棋
await fetch(`/api/game/${game.game_id}/move`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({row: 0, col: 0})
});
```

### cURL示例

```bash
# 创建游戏
curl -X POST http://localhost:5000/api/game/create \
  -H "Content-Type: application/json" \
  -d '{"player_x_type":"human","player_o_type":"ai"}'

# 下棋
curl -X POST http://localhost:5000/api/game/{game_id}/move \
  -H "Content-Type: application/json" \
  -d '{"row":0,"col":1}'

# 获取状态
curl http://localhost:5000/api/game/{game_id}/state

# 监听SSE (使用curl)
curl -N http://localhost:5000/api/game/{game_id}/events
```

---

## 注意事项

1. **SSE连接**: 建议为每个游戏保持一个SSE连接以接收实时更新
2. **游戏ID**: 创建游戏后保存game_id用于后续操作
3. **玩家类型**: 
   - `human`: 人类玩家，通过API手动下棋
   - `ai`: 内置AI，调用`/ai-move`端点
   - `agent`: 外部Agent，通过API接入
4. **并发**: 服务器支持多个游戏同时进行
5. **游戏清理**: 建议在游戏结束后删除不需要的游戏实例

---

## 支持

如有问题，请查看：
- README.md
- 示例代码: example_agent.py
- 测试代码: test_game.py
