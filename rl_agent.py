"""
强化学习Agent - 使用Stable-Baselines3
基于PPO算法训练井字棋AI，通过API接入井字棋决斗场
"""
import requests
import numpy as np
import time
import gymnasium as gym
from gymnasium import spaces
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.callbacks import BaseCallback
import os


class TicTacToeEnv(gym.Env):
    """井字棋强化学习环境"""
    
    def __init__(self, base_url='http://127.0.0.1:5000', opponent='ai'):
        super().__init__()
        
        self.base_url = base_url
        self.opponent = opponent  # 'ai' or 'random'
        self.game_id = None
        self.player = None  # 'X' or 'O'
        
        # 动作空间: 9个位置 (0-8)
        self.action_space = spaces.Discrete(9)
        
        # 状态空间: 3x3棋盘，每个位置可以是 0(空), 1(我方), -1(对方)
        # 展平为9维向量
        self.observation_space = spaces.Box(
            low=-1, high=1, shape=(9,), dtype=np.float32
        )
        
        # 设置HTTP会话
        self.session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.05,
                      status_forcelist=[429, 500, 502, 503, 504],
                      allowed_methods=["GET", "POST", "HEAD", "OPTIONS"])
        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # 统计信息
        self.episode_count = 0
        self.wins = 0
        self.losses = 0
        self.draws = 0
        
    def _create_game(self):
        """创建新游戏"""
        url = f'{self.base_url}/api/game/create'
        try:
            response = self.session.post(url, json={
                'player_x_type': 'agent',
                'player_o_type': self.opponent
            }, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                self.game_id = data['game_id']
                self.player = 'X'  # Agent总是X（先手）
                return True
            else:
                print(f"创建游戏失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"创建游戏异常: {e}")
            return False
    
    def _get_game_state(self):
        """获取游戏状态"""
        if not self.game_id:
            return None
        
        url = f'{self.base_url}/api/game/{self.game_id}/state'
        try:
            response = self.session.get(url, timeout=5)
            if response.status_code == 200:
                return response.json().get('game_state')
            return None
        except Exception as e:
            print(f"获取状态异常: {e}")
            return None
    
    def _make_move(self, row, col):
        """执行移动"""
        if not self.game_id:
            return False
        
        url = f'{self.base_url}/api/game/{self.game_id}/move'
        try:
            # 确保 row 和 col 是 Python int 类型，而不是 numpy int64
            response = self.session.post(url, json={
                'row': int(row),
                'col': int(col)
            }, timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"移动异常: {e}")
            return False
    
    def _request_ai_move(self):
        """请求AI下棋"""
        if not self.game_id:
            return False
        
        url = f'{self.base_url}/api/game/{self.game_id}/ai-move'
        try:
            response = self.session.post(url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"AI移动异常: {e}")
            return False
    
    def _board_to_observation(self, board, player):
        """
        将棋盘转换为观察向量
        board: 3x3列表，元素为 None, 'X', 'O'
        player: 当前Agent的玩家标识 ('X' or 'O')
        返回: 9维numpy数组，1=我方，-1=对方，0=空
        """
        obs = []
        for row in board:
            for cell in row:
                if cell is None:
                    obs.append(0)
                elif cell == player:
                    obs.append(1)  # 我方
                else:
                    obs.append(-1)  # 对方
        return np.array(obs, dtype=np.float32)
    
    def _action_to_position(self, action):
        """将动作(0-8)转换为棋盘位置(row, col)"""
        # 确保返回 Python int 类型
        return int(action // 3), int(action % 3)
    
    def _is_valid_action(self, action, board):
        """检查动作是否合法（位置是否为空）"""
        row, col = self._action_to_position(action)
        return board[row][col] is None
    
    def reset(self, seed=None, options=None):
        """重置环境，开始新游戏"""
        super().reset(seed=seed)
        
        self.episode_count += 1
        
        # 创建新游戏
        if not self._create_game():
            # 如果创建失败，返回空棋盘
            return np.zeros(9, dtype=np.float32), {}
        
        # 获取初始状态
        game_state = self._get_game_state()
        if game_state:
            board = game_state['board']
            obs = self._board_to_observation(board, self.player)
            return obs, {}
        
        return np.zeros(9, dtype=np.float32), {}
    
    def step(self, action):
        """执行一步动作"""
        game_state = self._get_game_state()
        if not game_state:
            return np.zeros(9, dtype=np.float32), -10, True, False, {}
        
        board = game_state['board']
        
        # 检查动作是否合法
        if not self._is_valid_action(action, board):
            # 非法移动，给予惩罚并结束
            obs = self._board_to_observation(board, self.player)
            return obs, -5, True, False, {'illegal_move': True}
        
        # 执行移动
        row, col = self._action_to_position(action)
        if not self._make_move(row, col):
            return np.zeros(9, dtype=np.float32), -10, True, False, {}
        
        time.sleep(0.05)  # 短暂等待服务器更新
        
        # 获取移动后的状态
        game_state = self._get_game_state()
        if not game_state:
            return np.zeros(9, dtype=np.float32), -10, True, False, {}
        
        board = game_state['board']
        status = game_state['status']
        
        # 检查游戏是否结束
        if status == 'finished':
            winner = game_state.get('winner')
            obs = self._board_to_observation(board, self.player)
            
            if winner == self.player:
                # 赢了
                self.wins += 1
                return obs, 10, True, False, {'result': 'win'}
            elif winner is None:
                # 平局
                self.draws += 1
                return obs, 0, True, False, {'result': 'draw'}
            else:
                # 输了
                self.losses += 1
                return obs, -10, True, False, {'result': 'loss'}
        
        # 游戏继续，请求对手下棋
        self._request_ai_move()
        time.sleep(0.05)
        
        # 获取对手下棋后的状态
        game_state = self._get_game_state()
        if not game_state:
            return np.zeros(9, dtype=np.float32), -10, True, False, {}
        
        board = game_state['board']
        status = game_state['status']
        obs = self._board_to_observation(board, self.player)
        
        # 再次检查游戏是否结束
        if status == 'finished':
            winner = game_state.get('winner')
            
            if winner == self.player:
                self.wins += 1
                return obs, 10, True, False, {'result': 'win'}
            elif winner is None:
                self.draws += 1
                return obs, 0, True, False, {'result': 'draw'}
            else:
                self.losses += 1
                return obs, -10, True, False, {'result': 'loss'}
        
        # 游戏继续，给予小奖励（活着就好）
        return obs, 0.1, False, False, {}
    
    def render(self, mode='human'):
        """渲染环境（可选）"""
        if mode == 'human' and self.game_id:
            print(f"游戏ID: {self.game_id}")
            print(f"访问: {self.base_url}")
    
    def close(self):
        """关闭环境"""
        self.session.close()


class TrainingCallback(BaseCallback):
    """训练过程回调，用于显示进度"""
    
    def __init__(self, verbose=0):
        super().__init__(verbose)
        self.episode_rewards = []
        self.episode_lengths = []
    
    def _on_step(self):
        # 每100步显示一次统计
        if self.n_calls % 100 == 0:
            # 从 DummyVecEnv 中获取被包装的环境
            vec_env = self.training_env.envs[0]
            # 如果环境被 Monitor 包装，需要访问 .env 获取原始环境
            if hasattr(vec_env, 'env'):
                env = vec_env.env
            else:
                env = vec_env
            
            total = env.wins + env.losses + env.draws
            if total > 0:
                win_rate = env.wins / total * 100
                print(f"\n步数: {self.n_calls} | "
                      f"回合: {env.episode_count} | "
                      f"胜: {env.wins} | 负: {env.losses} | 平: {env.draws} | "
                      f"胜率: {win_rate:.1f}%")
        return True


def train_agent(total_timesteps=10000, model_path='models/rl_agent_ppo'):
    """训练强化学习Agent"""
    print("="*60)
    print("井字棋强化学习训练 - Stable-Baselines3 PPO")
    print("="*60)
    print(f"\n训练步数: {total_timesteps}")
    print("对手: AI")
    print(f"模型保存路径: {model_path}\n")
    
    # 创建模型目录
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    
    # 创建环境
    env = TicTacToeEnv(opponent='ai')
    
    # 检查环境是否符合Gym规范
    print("检查环境...")
    check_env(env, warn=True)
    print("✓ 环境检查通过\n")
    
    # 创建或加载模型
    if os.path.exists(f"{model_path}.zip"):
        print(f"加载已有模型: {model_path}.zip")
        model = PPO.load(model_path, env=env)
    else:
        print("创建新模型...")
        model = PPO(
            "MlpPolicy",
            env,
            verbose=1,
            learning_rate=0.0003,
            n_steps=2048,
            batch_size=64,
            n_epochs=10,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.01,
        )
    
    # 训练
    print("\n开始训练...\n")
    callback = TrainingCallback()
    
    # 保存对原始环境的引用（在被包装之前）
    original_env = env
    
    model.learn(total_timesteps=total_timesteps, callback=callback)
    
    # 保存模型
    model.save(model_path)
    print(f"\n✓ 模型已保存: {model_path}.zip")
    
    # 显示最终统计（使用原始环境引用）
    print("\n" + "="*60)
    print("训练完成！")
    print("="*60)
    total = original_env.wins + original_env.losses + original_env.draws
    if total > 0:
        print(f"总回合: {original_env.episode_count}")
        print(f"胜利: {original_env.wins} ({original_env.wins/total*100:.1f}%)")
        print(f"失败: {original_env.losses} ({original_env.losses/total*100:.1f}%)")
        print(f"平局: {original_env.draws} ({original_env.draws/total*100:.1f}%)")
    
    original_env.close()
    return model


def test_agent(model_path='models/rl_agent_ppo', num_games=10):
    """测试训练好的Agent"""
    print("="*60)
    print("测试强化学习Agent")
    print("="*60)
    print(f"模型: {model_path}.zip")
    print(f"测试局数: {num_games}\n")
    
    # 加载环境和模型
    env = TicTacToeEnv(opponent='ai')
    
    if not os.path.exists(f"{model_path}.zip"):
        print(f"✗ 模型不存在: {model_path}.zip")
        print("请先运行训练: python rl_agent.py --train")
        return
    
    model = PPO.load(model_path)
    
    # 测试
    wins = 0
    losses = 0
    draws = 0
    
    for i in range(num_games):
        obs, _ = env.reset()
        done = False
        
        print(f"\n第 {i+1} 局游戏 (ID: {env.game_id})")
        
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, truncated, info = env.step(action)
            
            if done:
                result = info.get('result', 'unknown')
                if result == 'win':
                    wins += 1
                    print(f"  ✓ 胜利！奖励: {reward}")
                elif result == 'loss':
                    losses += 1
                    print(f"  ✗ 失败。奖励: {reward}")
                elif result == 'draw':
                    draws += 1
                    print(f"  - 平局。奖励: {reward}")
                elif info.get('illegal_move'):
                    losses += 1
                    print(f"  ✗ 非法移动。奖励: {reward}")
        
        time.sleep(1)  # 游戏间隔
    
    # 显示统计
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)
    print(f"总局数: {num_games}")
    print(f"胜利: {wins} ({wins/num_games*100:.1f}%)")
    print(f"失败: {losses} ({losses/num_games*100:.1f}%)")
    print(f"平局: {draws} ({draws/num_games*100:.1f}%)")
    
    env.close()


def play_interactive(model_path='models/rl_agent_ppo'):
    """交互式对战 - 持续玩游戏"""
    print("="*60)
    print("强化学习Agent - 连续对战模式")
    print("="*60)
    print(f"模型: {model_path}.zip")
    print("按 Ctrl+C 退出\n")
    
    # 加载环境和模型
    env = TicTacToeEnv(opponent='ai')
    
    if not os.path.exists(f"{model_path}.zip"):
        print(f"✗ 模型不存在: {model_path}.zip")
        print("请先运行训练: python rl_agent.py --train")
        return
    
    model = PPO.load(model_path)
    
    game_count = 0
    
    try:
        while True:
            game_count += 1
            print(f"\n{'='*60}")
            print(f"第 {game_count} 局游戏")
            print(f"{'='*60}")
            
            obs, _ = env.reset()
            done = False
            
            print(f"游戏ID: {env.game_id}")
            print(f"访问 {env.base_url} 观看对战\n")
            
            step_count = 0
            while not done:
                action, _ = model.predict(obs, deterministic=True)
                obs, reward, done, truncated, info = env.step(action)
                step_count += 1
                
                if done:
                    result = info.get('result', 'unknown')
                    if result == 'win':
                        print(f"🎉 第 {game_count} 局: 胜利！({step_count} 步)")
                    elif result == 'loss':
                        print(f"😢 第 {game_count} 局: 失败。({step_count} 步)")
                    elif result == 'draw':
                        print(f"🤝 第 {game_count} 局: 平局。({step_count} 步)")
            
            # 显示累计统计
            total = env.wins + env.losses + env.draws
            if total > 0:
                print(f"\n累计统计: 胜 {env.wins} | 负 {env.losses} | 平 {env.draws} | "
                      f"胜率 {env.wins/total*100:.1f}%")
            
            # 等待下一局
            time.sleep(3)
    
    except KeyboardInterrupt:
        print(f"\n\n👋 程序已退出 (共玩了 {game_count} 局)")
        total = env.wins + env.losses + env.draws
        if total > 0:
            print(f"最终统计: 胜 {env.wins} | 负 {env.losses} | 平 {env.draws} | "
                  f"胜率 {env.wins/total*100:.1f}%")
    
    env.close()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == '--train':
            # 训练模式
            timesteps = int(sys.argv[2]) if len(sys.argv) > 2 else 10000
            train_agent(total_timesteps=timesteps)
        
        elif command == '--test':
            # 测试模式
            num_games = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            test_agent(num_games=num_games)
        
        elif command == '--play':
            # 连续对战模式
            play_interactive()
        
        else:
            print("未知命令！")
            print("\n使用方法:")
            print("  训练: python rl_agent.py --train [步数]")
            print("  测试: python rl_agent.py --test [局数]")
            print("  对战: python rl_agent.py --play")
    
    else:
        # 默认：训练模式
        print("使用方法:")
        print("  训练: python rl_agent.py --train [步数]")
        print("  测试: python rl_agent.py --test [局数]")
        print("  对战: python rl_agent.py --play")
        print("\n运行默认训练...")
        train_agent(total_timesteps=5000)
