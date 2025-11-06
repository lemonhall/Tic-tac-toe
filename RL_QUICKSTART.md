# 强化学习 Agent 快速上手 ⚡

## 🎯 一分钟快速开始

### 方式 A: 使用 PowerShell 脚本（推荐）

```powershell
# 1. 启动服务器（在一个终端）
.\start.ps1

# 2. 快速演示（在另一个终端）
.\demo_rl.ps1
```

### 方式 B: 手动执行

```powershell
# 1. 启动服务器
python app.py

# 2. 安装依赖（新终端）
pip install -r requirements-rl.txt

# 3. 训练
python rl_agent.py --train 5000

# 4. 测试
python rl_agent.py --test 10

# 5. 对战
python rl_agent.py --play
```

---

## 📦 依赖安装

### 方法 1: 一键安装所有依赖
```powershell
pip install -r requirements.txt
pip install -r requirements-rl.txt
```

### 方法 2: 手动安装核心依赖
```powershell
pip install stable-baselines3==2.2.1
pip install gymnasium==0.29.1
pip install numpy==1.24.3
```

---

## 🎮 使用示例

### 示例 1: 快速训练和测试
```powershell
# 训练 5000 步（约 2-3 分钟）
python rl_agent.py --train 5000

# 测试 10 局
python rl_agent.py --test 10
```

### 示例 2: 充分训练
```powershell
# 训练 50000 步（约 20-30 分钟，更高胜率）
python rl_agent.py --train 50000

# 测试 50 局看效果
python rl_agent.py --test 50
```

### 示例 3: 实时观战
```powershell
# 1. 启动对战模式
python rl_agent.py --play

# 2. 在浏览器打开 http://localhost:5000
# 3. 选择"观战模式"，输入显示的游戏 ID
```

### 示例 4: 继续训练
```powershell
# 模型会自动保存，再次训练会从上次继续
python rl_agent.py --train 10000  # 第一次训练
python rl_agent.py --train 10000  # 继续训练（累计 20000 步）
```

---

## 📊 预期效果

| 训练步数 | 训练时间 | 预期胜率 | 说明 |
|---------|---------|---------|------|
| 1,000 | ~30秒 | 20-30% | 初步学习 |
| 5,000 | ~2分钟 | 40-50% | 基本策略 |
| 10,000 | ~5分钟 | 50-60% | 较好策略 |
| 20,000 | ~10分钟 | 60-70% | 优秀策略 |
| 50,000+ | ~30分钟 | 70-80% | 接近最优 |

---

## 🔍 实时监控

训练过程中会显示实时统计：

```
步数: 100 | 回合: 15 | 胜: 3 | 负: 10 | 平: 2 | 胜率: 20.0%
步数: 200 | 回合: 30 | 胜: 8 | 负: 18 | 平: 4 | 胜率: 26.7%
步数: 500 | 回合: 75 | 胜: 25 | 负: 42 | 平: 8 | 胜率: 33.3%
...
步数: 5000 | 回合: 750 | 胜: 375 | 负: 300 | 平: 75 | 胜率: 50.0%
```

---

## ⚙️ 常用参数

### 训练步数建议
- **快速测试**: 1000-5000 步
- **日常训练**: 10000-20000 步
- **充分训练**: 50000+ 步

### 测试局数建议
- **快速验证**: 10 局
- **可靠评估**: 50 局
- **完整评估**: 100 局

---

## 🎯 训练技巧

### 1. 渐进式训练
```powershell
python rl_agent.py --train 5000   # 基础训练
python rl_agent.py --test 20      # 测试效果
python rl_agent.py --train 10000  # 继续训练
python rl_agent.py --test 50      # 再次测试
```

### 2. 观察学习过程
在训练时同时打开浏览器观看对战过程：
- 可以看到 Agent 从随机到有策略的进化
- 观察 Agent 如何学会占据中心、角落
- 看到 Agent 学会防守和进攻

### 3. 保存检查点
```python
# 可以修改 rl_agent.py 添加定期保存
# 在 train_agent() 函数中:
# model.save(f"{model_path}_checkpoint_{step}")
```

---

## 🐛 故障排除

### 问题: 训练很慢
**解决方案**:
```powershell
# 减少训练步数先测试
python rl_agent.py --train 1000
```

### 问题: 内存不足
**解决方案**:
- 减少 batch_size
- 减少 n_steps
- 关闭其他应用

### 问题: 模型不收敛
**解决方案**:
```powershell
# 删除旧模型重新训练
Remove-Item models/rl_agent_ppo.zip
python rl_agent.py --train 20000
```

### 问题: 非法移动太多
**解决方案**:
- 训练更多步数
- 修改奖励函数增加非法移动惩罚

---

## 📚 进阶阅读

详细文档请参考：
- [RL_AGENT_README.md](RL_AGENT_README.md) - 完整使用指南
- [README.md](README.md) - 项目整体说明

---

## 💡 小贴士

1. ✅ **先训练再测试** - 不要期望未训练的模型有好表现
2. ✅ **多训练几次** - 强化学习需要大量试错
3. ✅ **实时观战** - 能直观看到学习效果
4. ✅ **保存模型** - 模型会自动保存，可以继续训练
5. ✅ **调整超参数** - 不满意可以修改学习率等参数

---

## 🎉 成功案例

训练 50000 步后的典型表现：
- ✅ 几乎不再非法移动（<1%）
- ✅ 优先占据中心（>90%）
- ✅ 能识别获胜机会（>95%）
- ✅ 能阻止对手三连（>90%）
- ✅ 对抗内置 AI 胜率 70%+

---

祝您训练成功！🚀
有问题请查看 RL_AGENT_README.md 或提交 Issue。
