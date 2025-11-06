"""
让 RL Agent 和人类对弈并学习
Agent 会从和你的对局中学习，变得更强！
"""
import requests
import numpy as np
import time
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.common.maskable.policies import MaskableActorCriticPolicy
import gymnasium as gym
from gymnasium import spaces
import sys
import os
from datetime import datetime
import hashlib

class HumanOpponentEnv(gym.Env):
    """和人类对弈的环境"""
    
    def __init__(self, base_url='http://127.0.0.1:5000'):
        super().__init__()
        
        self.base_url = base_url
        self.session = requests.Session()
        self.game_id = None
        self.player = 'O'  # Agent 默认是 O
        self.current_board = None
        
        # 动作空间和状态空间
        self.action_space = spaces.Discrete(9)
        self.observation_space = spaces.Box(
            low=-1, high=1, shape=(9,), dtype=np.float32
        )
        
        # 统计
        self.episode_count = 0
        self.wins = 0
        self.losses = 0
        self.draws = 0
        
        print("🎮 人类对手环境初始化完成")
        print("请在浏览器中创建 '外部Agent vs 人类' 游戏")
    
    def _board_to_observation(self, board, player):
        """将棋盘转换为观察向量"""
        obs = []
        for row in board:
            for cell in row:
                if cell is None:
                    obs.append(0)
                elif cell == player:
                    obs.append(1)
                else:
                    obs.append(-1)
        return np.array(obs, dtype=np.float32)
    
    def _action_to_position(self, action):
        """将动作转换为位置"""
        return int(action // 3), int(action % 3)
    
    def action_masks(self):
        """获取动作掩码"""
        if self.current_board is None:
            return np.ones(9, dtype=np.bool_)
        
        masks = []
        for row in self.current_board:
            for cell in row:
                masks.append(cell is None)
        return np.array(masks, dtype=np.bool_)
    
    def reset(self, seed=None, options=None):
        """重置环境 - 等待新游戏"""
        super().reset(seed=seed)
        
        self.episode_count += 1
        
        # 等待人类创建新游戏
        print(f"\n{'='*60}")
        print(f"🎮 第 {self.episode_count} 局")
        print(f"{'='*60}")
        print("💡 在浏览器中:")
        print("   1. 选择 '外部Agent vs 人类' (Agent 先手)")
        print("   2. 点击 '开始游戏'")
        print("   3. Agent 会自动检测并开始")
        print("\n⏳ 等待新游戏...")
        
        # 轮询等待新游戏
        while True:
            time.sleep(1)
            
            response = self.session.get(f'{self.base_url}/api/games?status=in_progress')
            if response.status_code != 200:
                continue
            
            games = response.json().get('games', {})
            
            # 查找 Agent 是 X 的新游戏
            for game_id, game_info in games.items():
                if game_info['player_x_type'] == 'agent' and game_info['move_count'] == 0:
                    self.game_id = game_id
                    self.player = 'X'
                    print(f"✓ 检测到新游戏: {game_id}")
                    print(f"   Agent 扮演 {self.player}，准备先手！\n")
                    
                    # 获取初始状态
                    response = self.session.get(f'{self.base_url}/api/game/{game_id}/state')
                    game_state = response.json()['game_state']
                    self.current_board = game_state['board']
                    
                    obs = self._board_to_observation(self.current_board, self.player)
                    return obs, {}
        
    def step(self, action):
        """执行动作"""
        # Agent 下棋
        row, col = self._action_to_position(action)
        
        response = self.session.post(
            f'{self.base_url}/api/game/{self.game_id}/move',
            json={'row': int(row), 'col': int(col)}
        )
        
        if response.status_code != 200:
            # 非法移动
            print(f"❌ 非法移动: ({row}, {col})")
            return np.zeros(9, dtype=np.float32), -5, True, False, {'result': 'illegal'}
        
        print(f"🤖 Agent ({self.player}) 下在: ({row}, {col})")
        
        # 获取状态
        response = self.session.get(f'{self.base_url}/api/game/{self.game_id}/state')
        game_state = response.json()['game_state']
        self.current_board = game_state['board']
        status = game_state['status']
        
        # 检查游戏是否结束
        if status == 'finished':
            winner = game_state.get('winner')
            obs = self._board_to_observation(self.current_board, self.player)
            
            if winner == self.player:
                self.wins += 1
                print("🎉 Agent 赢了！")
                return obs, 20, True, False, {'result': 'win'}
            elif winner is None:
                self.draws += 1
                print("🤝 平局")
                return obs, 2, True, False, {'result': 'draw'}
            else:
                self.losses += 1
                print("😢 Agent 输了")
                return obs, -15, True, False, {'result': 'loss'}
        
        # 等待人类下棋
        print("   等待人类下棋...")
        while True:
            time.sleep(0.5)
            
            response = self.session.get(f'{self.base_url}/api/game/{self.game_id}/state')
            game_state = response.json()['game_state']
            status = game_state['status']
            current_player = game_state['current_player']
            
            # 游戏结束
            if status == 'finished':
                self.current_board = game_state['board']
                winner = game_state.get('winner')
                obs = self._board_to_observation(self.current_board, self.player)
                
                if winner == self.player:
                    self.wins += 1
                    print("🎉 Agent 赢了！")
                    return obs, 20, True, False, {'result': 'win'}
                elif winner is None:
                    self.draws += 1
                    print("🤝 平局")
                    return obs, 2, True, False, {'result': 'draw'}
                else:
                    self.losses += 1
                    print("😢 Agent 输了")
                    return obs, -15, True, False, {'result': 'loss'}
            
            # 轮到 Agent
            if current_player == self.player:
                self.current_board = game_state['board']
                obs = self._board_to_observation(self.current_board, self.player)
                return obs, 0.1, False, False, {}
    
    def close(self):
        self.session.close()


def _file_hash(path: str) -> str:
    """计算文件短哈希用于变化确认"""
    if not os.path.exists(path):
        return 'NA'
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()[:8]


def train_with_human(total_games=10, model_path='models/rl_agent_v2_ppo', save_every=1, checkpoint_dir='models/human_sessions'):
    """和人类对弈并学习"""
    print("="*60)
    print("🎓 和人类对弈训练模式")
    print("="*60)
    print(f"\n训练局数: {total_games}")
    print(f"模型路径: {model_path}\n")
    print(f"保存频率: 每 {save_every} 局 (含最后一局强制保存)")
    print(f"Checkpoint 目录: {checkpoint_dir}\n")

    # 确保 checkpoint 目录存在
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    # 创建环境
    env = HumanOpponentEnv()
    env = ActionMasker(env, lambda e: e.action_masks())
    
    # 加载已有模型
    if os.path.exists(f"{model_path}.zip"):
        print(f"✓ 加载已有模型: {model_path}.zip")
        model = MaskablePPO.load(model_path, env=env)
        print("✓ 模型会在和你对弈中继续学习！\n")
    else:
        print("❌ 找不到模型，从零开始训练")
        model = MaskablePPO(
            MaskableActorCriticPolicy,
            env,
            verbose=1,
            learning_rate=0.0003,
        )
    
    print("="*60)
    print("开始训练！")
    print("="*60)
    
    # 训练多局
    base_file = f"{model_path}.zip"
    previous_hash = _file_hash(base_file)
    for game_num in range(total_games):
        obs, _ = env.reset()
        done = False
        
        while not done:
            # Agent 下棋
            action_masks = env.action_masks()
            action, _ = model.predict(obs, action_masks=action_masks, deterministic=False)
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            
            # 学习！
            if done:
                print(f"\n📚 学习中...")
                # 增加学习步数，确保模型真正学到东西
                model.learn(total_timesteps=500, reset_num_timesteps=False)
                print(f"✓ 学习完成 (更新了 500 步)\n")
        
        # 显示统计
        total = env.wins + env.losses + env.draws
        if total > 0:
            print(f"\n📊 累计战绩:")
            print(f"   胜: {env.wins} ({env.wins/total*100:.1f}%)")
            print(f"   负: {env.losses} ({env.losses/total*100:.1f}%)")
            print(f"   平: {env.draws} ({env.draws/total*100:.1f}%)")
        
        # 保存逻辑（可配置频率，默认每局）
        if (game_num + 1) % save_every == 0:
            print(f"\n💾 保存中 (第 {game_num + 1}/{total_games} 局) ...", end='')
            sys.stdout.flush()
            model.save(model_path)
            # 生成 checkpoint 文件（带局号）
            ck_name = f"{os.path.basename(model_path)}_g{game_num + 1:04d}"
            ck_path_nozip = os.path.join(checkpoint_dir, ck_name)
            model.save(ck_path_nozip)
            # 确认文件更新时间与哈希
            if os.path.exists(base_file):
                mtime = os.path.getmtime(base_file)
                time_str = datetime.fromtimestamp(mtime).strftime('%H:%M:%S')
                new_hash = _file_hash(base_file)
                changed = '✔' if new_hash != previous_hash else '⚠ 未变化'
                print(f" 完成\n   主模型时间: {time_str}  哈希: {new_hash}  变化: {changed}")
                ck_file = f"{ck_path_nozip}.zip"
                if os.path.exists(ck_file):
                    ck_mtime = os.path.getmtime(ck_file)
                    ck_time = datetime.fromtimestamp(ck_mtime).strftime('%H:%M:%S')
                    print(f"   Checkpoint: {ck_file} 时间: {ck_time}")
                previous_hash = new_hash
            else:
                print(" ⚠ 未找到主模型文件，保存可能失败")
            sys.stdout.flush()
    
    # 最终保存模型（冗余一次确保落盘）
    print(f"\n💾 最终保存确认...")
    model.save(model_path)
    final_hash = _file_hash(base_file)
    print(f"✅ 训练完成！模型: {base_file} 最终哈希: {final_hash}")
    print(f"\n🎓 Agent 从你这里学到了 {total_games} 局的经验！")
    print(f"   总学习步数(理论): {total_games * 500} 步")
    
    env.close()


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎓 人类教练模式")
    print("="*60)
    print("\n让 RL Agent 和你对弈并学习！")
    print("Agent 会从你的棋路中学习，变得更强！\n")
    
    # 解析参数
    if len(sys.argv) > 1:
        games = int(sys.argv[1])
    else:
        games = 10
    
    print(f"训练局数: {games}")
    print("(可以用 Ctrl+C 随时中断)\n")
    
    try:
        train_with_human(total_games=games)
    except KeyboardInterrupt:
        print("\n\n👋 训练中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
