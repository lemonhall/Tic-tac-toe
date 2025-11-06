# 快速启动指南

## 🚀 5分钟快速开始

### 步骤1: 安装依赖

打开PowerShell，进入项目目录：

```powershell
cd e:\development\Tic-tac-toe
pip install -r requirements.txt
```

### 步骤2: 启动服务器

**方式A - 使用启动脚本**:
```powershell
.\start.ps1
```

**方式B - 手动启动**:
```powershell
python app.py
```

### 步骤3: 打开浏览器

访问: http://localhost:5000

### 步骤4: 开始游戏！

1. 选择游戏模式（人类vs人类 / 人类vsAI / AIvsAI / 观战）
2. 点击"开始游戏"
3. 在棋盘上点击下棋

---

## 🎮 游戏模式说明

### 👤 vs 👤 (人类 vs 人类)
- 两个玩家轮流在同一设备上下棋
- 适合本地对战

### 👤 vs 🤖 (人类 vs AI)
- 你对抗内置AI
- AI使用智能策略

### 🤖 vs 🤖 (AI vs AI)
- 观看两个AI对战
- 自动进行

### 👁️ 观战模式
- 纯观看模式
- 不能下棋

---

## 🧪 运行测试

测试游戏逻辑和AI：

```powershell
python test_game.py
```

---

## 🤖 接入外部Agent

### 1. 运行示例Agent

```powershell
pip install -r requirements.txt
python example_agent.py
```

### 2. 自定义Agent

参考 `example_agent.py` 编写你自己的Agent：

```python
import requests

# 创建游戏
response = requests.post('http://localhost:5000/api/game/create',
    json={'player_x_type': 'agent', 'player_o_type': 'ai'})
game_id = response.json()['game_id']

# 监听事件
url = f'http://localhost:5000/api/game/{game_id}/events'
# ... 监听SSE事件

# 下棋
requests.post(f'http://localhost:5000/api/game/{game_id}/move',
    json={'row': 0, 'col': 0})
```

---

## 📚 更多文档

- **完整文档**: README.md
- **API文档**: API.md
- **示例代码**: example_agent.py
- **测试代码**: test_game.py

---

## ❓ 常见问题

### Q: 端口被占用怎么办？
A: 修改 `app.py` 中的端口号：
```python
app.run(host='0.0.0.0', port=5001, debug=True)
```

### Q: 如何查看日志？
A: 查看终端输出，所有操作都有日志记录

### Q: 如何停止服务器？
A: 在终端按 `Ctrl+C`

### Q: SSE连接失败？
A: 确保浏览器支持EventSource，检查控制台错误

---

## 🎯 下一步

✅ 熟悉Web界面  
✅ 尝试不同游戏模式  
✅ 查看API文档  
✅ 编写你的AI Agent  
✅ 接入RL系统或LLM  

---

**享受游戏！** 🎮
