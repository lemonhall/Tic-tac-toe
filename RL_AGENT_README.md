# 强化学习 Agent 使用指南

## 📖 简介

这是一个基于 **Stable-Baselines3** 的强化学习井字棋 Agent，使用 **PPO (Proximal Policy Optimization)** 算法训练。

Agent 通过与井字棋决斗场服务器的 API 交互来学习最优策略。

---

## 🚀 快速开始

### 1. 安装依赖

首先确保已安装基础依赖：
```powershell
pip install -r requirements.txt
```

然后安装强化学习相关依赖：
```powershell
pip install -r requirements-rl.txt
```

### 2. 启动服务器

在另一个终端窗口启动游戏服务器：
```powershell
python app.py
```

### 3. 训练 Agent

训练 5000 步（默认）：
```powershell
python rl_agent.py --train
```

训练指定步数（例如 20000 步）：
```powershell
python rl_agent.py --train 20000
```

### 4. 测试 Agent

测试 10 局（默认）：
```powershell
python rl_agent.py --test
```

测试指定局数（例如 50 局）：
```powershell
python rl_agent.py --test 50
```

### 5. 连续对战模式

让训练好的 Agent 持续与 AI 对战：
```powershell
python rl_agent.py --play
```

按 `Ctrl+C` 退出。

---

## 🎯 工作原理

### 环境设计

**TicTacToeEnv** 是一个符合 Gymnasium 标准的强化学习环境：

- **状态空间**: 9 维向量，表示 3x3 棋盘
  - `1`: 我方棋子
  - `-1`: 对方棋子
  - `0`: 空位

- **动作空间**: 离散动作，9 个位置 (0-8)
  ```
  0 | 1 | 2
  ---------
  3 | 4 | 5
  ---------
  6 | 7 | 8
  ```

- **奖励设计**:
  - 胜利: `+10`
  - 失败: `-10`
  - 平局: `0`
  - 非法移动: `-5`（游戏结束）
  - 合法移动（游戏继续）: `+0.1`

### PPO 算法

使用 **PPO** (Proximal Policy Optimization) 算法：
- 稳定且高效的策略梯度算法
- 适合离散动作空间
- 使用经验回放缓冲区

### 训练流程

```
Agent 创建游戏 → 
获取初始状态 → 
Agent 选择动作 → 
执行移动 → 
对手（AI）移动 → 
获取新状态和奖励 → 
重复直到游戏结束 → 
更新策略 → 
开始新游戏
```

---

## 📊 训练建议

### 训练步数

- **快速测试**: 5,000 步（约 100-200 局）
- **基础训练**: 20,000 步（约 400-800 局）
- **充分训练**: 50,000+ 步（约 1000+ 局）

### 超参数调整

在 `rl_agent.py` 的 `train_agent()` 函数中可以调整：

```python
model = PPO(
    "MlpPolicy",
    env,
    learning_rate=0.0003,    # 学习率
    n_steps=2048,            # 每次更新收集的步数
    batch_size=64,           # 批量大小
    n_epochs=10,             # 每次更新的epoch数
    gamma=0.99,              # 折扣因子
    gae_lambda=0.95,         # GAE参数
    clip_range=0.2,          # PPO裁剪范围
    ent_coef=0.01,           # 熵系数（鼓励探索）
)
```

### 对手选择

可以修改对手类型：
```python
env = TicTacToeEnv(opponent='ai')  # 使用内置AI
```

---

## 📁 文件结构

```
rl_agent.py              # 主程序
requirements-rl.txt      # 强化学习依赖
models/
  └── rl_agent_ppo.zip   # 训练好的模型（自动生成）
```

---

## 🔍 查看训练过程

### 实时监控

训练时会每 100 步显示一次统计：
```
步数: 100 | 回合: 15 | 胜: 3 | 负: 10 | 平: 2 | 胜率: 20.0%
步数: 200 | 回合: 30 | 胜: 8 | 负: 18 | 平: 4 | 胜率: 26.7%
...
```

### TensorBoard（可选）

如果想查看详细训练曲线：
```powershell
tensorboard --logdir ./logs
```

---

## 🎮 实时观看对战

1. 在浏览器打开: http://localhost:5000
2. 运行 Agent: `python rl_agent.py --play`
3. 在浏览器中选择"观战模式"并输入游戏ID

---

## 💡 进阶技巧

### 1. 继续训练

模型会自动保存在 `models/rl_agent_ppo.zip`。再次运行训练会加载已有模型继续训练：
```powershell
python rl_agent.py --train 10000
```

### 2. 自对弈训练

修改代码创建两个Agent互相对战（更高级的训练方式）。

### 3. 课程学习

先让Agent对抗简单对手（随机），再逐步提升难度。

### 4. 奖励塑造

调整奖励函数，例如：
- 给予占据中心位置额外奖励
- 根据移动质量给予奖励
- 惩罚重复无意义的移动

---

## 🐛 常见问题

### Q: 训练很慢怎么办？

A: 减少 `n_steps` 或增加 `batch_size`，或者减少训练步数。

### Q: Agent 总是非法移动？

A: 增加非法移动的惩罚（`-5` → `-10`），或训练更多步数。

### Q: 胜率无法提升？

A: 
- 增加训练步数
- 调整学习率
- 调整奖励函数
- 尝试不同的超参数

### Q: 内存占用太大？

A: 减少 `n_steps` 参数。

---

## 📚 参考资料

- [Stable-Baselines3 文档](https://stable-baselines3.readthedocs.io/)
- [Gymnasium 文档](https://gymnasium.farama.org/)
- [PPO 论文](https://arxiv.org/abs/1707.06347)

---

## 🎓 学习路径

1. ✅ 理解强化学习基础概念
2. ✅ 运行默认训练看看效果
3. ✅ 修改奖励函数观察影响
4. ✅ 调整超参数优化性能
5. ✅ 尝试不同算法（DQN, A2C等）
6. ✅ 实现更复杂的对战策略

---

## 🤝 与原 Agent 对比

| 特性 | example_agent.py | rl_agent.py |
|------|-----------------|-------------|
| 策略 | 随机 | 强化学习（智能） |
| 学习能力 | ❌ 无 | ✅ 能学习和改进 |
| 胜率 | ~10% | 训练后可达 60-80% |
| 依赖 | 基础库 | 需要 SB3 + Gymnasium |
| 训练时间 | 无需训练 | 需要训练 |
| 适用场景 | 测试、演示 | 研究、竞技 |

---

## 📈 预期效果

经过充分训练（50000+ 步）后，Agent 应该能：

- ✅ 几乎不再犯非法移动错误
- ✅ 优先占据中心和角落
- ✅ 能识别并阻止对手的三连
- ✅ 能创造自己的获胜机会
- ✅ 对抗内置 AI 达到 60-80% 胜率

---

祝您训练愉快！🚀
