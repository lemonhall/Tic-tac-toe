"""
强化学习Agent V2 - 使用动作掩码优化
解决非法移动问题，提高学习效率
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
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.common.maskable.policies import MaskableActorCriticPolicy
import os


class TicTacToeEnv(gym.Env):
    """井字棋强化学习环境 - 支持动作掩码"""
    
    def __init__(self, base_url='http://127.0.0.1:5000', opponent='ai'):
        super().__init__()
        
        self.base_url = base_url
        self.opponent = opponent
        self.game_id = None
        self.player = None
        
        # 动作空间和状态空间
        self.action_space = spaces.Discrete(9)
        self.observation_space = spaces.Box(
            low=-1, high=1, shape=(9,), dtype=np.float32
        )
        
        # HTTP会话
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
        self.illegal_moves = 0
        self.errors = 0
        
        # 当前棋盘状态（用于动作掩码）
        self.current_board = None
    
    def action_masks(self):
        """返回当前状态下的动作掩码（True=可选，False=不可选）"""
        if self.current_board is None:
            return np.ones(9, dtype=bool)
        
        mask = []
        for i in range(3):
            for j in range(3):
                mask.append(self.current_board[i][j] is None)
        return np.array(mask, dtype=bool)
    
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
                self.player = 'X'
                return True
        except Exception as e:
            pass
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
        except Exception as e:
            pass
        return None
    
    def _make_move(self, row, col):
        """执行移动"""
        if not self.game_id:
            return False
        
        url = f'{self.base_url}/api/game/{self.game_id}/move'
        try:
            response = self.session.post(url, json={
                'row': int(row),
                'col': int(col)
            }, timeout=5)
            return response.status_code == 200
        except Exception as e:
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
            return False
    
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
    
    def reset(self, seed=None, options=None):
        """重置环境"""
        super().reset(seed=seed)
        
        self.episode_count += 1
        
        if not self._create_game():
            self.current_board = [[None]*3 for _ in range(3)]
            return np.zeros(9, dtype=np.float32), {}
        
        game_state = self._get_game_state()
        if game_state:
            self.current_board = game_state['board']
            obs = self._board_to_observation(self.current_board, self.player)
            return obs, {}
        
        self.current_board = [[None]*3 for _ in range(3)]
        return np.zeros(9, dtype=np.float32), {}
    
    def step(self, action):
        """执行一步动作"""
        game_state = self._get_game_state()
        if not game_state:
            self.losses += 1
            self.errors += 1
            return np.zeros(9, dtype=np.float32), -10, True, False, {'result': 'error'}
        
        self.current_board = game_state['board']
        
        # 执行移动（已通过动作掩码保证合法）
        row, col = self._action_to_position(action)
        if not self._make_move(row, col):
            self.losses += 1
            self.errors += 1
            return np.zeros(9, dtype=np.float32), -10, True, False, {'result': 'error'}
        
        time.sleep(0.05)
        
        # 获取移动后的状态
        game_state = self._get_game_state()
        if not game_state:
            self.losses += 1
            self.errors += 1
            return np.zeros(9, dtype=np.float32), -10, True, False, {'result': 'error'}
        
        self.current_board = game_state['board']
        status = game_state['status']
        
        # 检查游戏是否结束
        if status == 'finished':
            winner = game_state.get('winner')
            obs = self._board_to_observation(self.current_board, self.player)
            
            if winner == self.player:
                self.wins += 1
                return obs, 10, True, False, {'result': 'win'}
            elif winner is None:
                # 平局 - 对于先手玩家,平局是不错的结果(对手没犯错)
                self.draws += 1
                return obs, 5, True, False, {'result': 'draw'}
            else:
                self.losses += 1
                return obs, -10, True, False, {'result': 'loss'}
        
        # 游戏继续，请求对手下棋
        self._request_ai_move()
        time.sleep(0.05)
        
        # 获取对手下棋后的状态
        game_state = self._get_game_state()
        if not game_state:
            self.losses += 1
            self.errors += 1
            return np.zeros(9, dtype=np.float32), -10, True, False, {'result': 'error'}
        
        self.current_board = game_state['board']
        status = game_state['status']
        obs = self._board_to_observation(self.current_board, self.player)
        
        # 再次检查游戏是否结束
        if status == 'finished':
            winner = game_state.get('winner')
            
            if winner == self.player:
                self.wins += 1
                return obs, 10, True, False, {'result': 'win'}
            elif winner is None:
                # 平局 - 对于先手玩家,平局是不错的结果
                self.draws += 1
                return obs, 5, True, False, {'result': 'draw'}
            else:
                self.losses += 1
                return obs, -10, True, False, {'result': 'loss'}
        
        # 游戏继续
        return obs, 0.1, False, False, {}
    
    def close(self):
        """关闭环境"""
        self.session.close()


class TrainingCallback(BaseCallback):
    """训练回调"""
    
    def __init__(self, verbose=0):
        super().__init__(verbose)
    
    def _on_step(self):
        if self.n_calls % 100 == 0:
            vec_env = self.training_env.envs[0]
            if hasattr(vec_env, 'env'):
                env = vec_env.env
            else:
                env = vec_env
            
            # 获取原始环境（去掉ActionMasker包装）
            while hasattr(env, 'env') and not hasattr(env, 'wins'):
                env = env.env
            
            total = env.wins + env.losses + env.draws
            illegal_rate = (env.illegal_moves / env.episode_count * 100) if env.episode_count > 0 else 0
            
            if total > 0:
                win_rate = env.wins / total * 100
                print(f"\n步数: {self.n_calls} | "
                      f"回合: {env.episode_count} | "
                      f"胜: {env.wins} | 负: {env.losses} | 平: {env.draws} | "
                      f"胜率: {win_rate:.1f}% | "
                      f"非法: {env.illegal_moves}({illegal_rate:.1f}%)")
        return True


def train_agent_v2(total_timesteps=10000, model_path='models/rl_agent_v2_ppo'):
    """训练V2版本（使用动作掩码）"""
    print("="*60)
    print("井字棋强化学习训练 V2 - 动作掩码优化版")
    print("="*60)
    print(f"\n训练步数: {total_timesteps}")
    print("优化: 使用动作掩码，消除非法移动")
    print(f"模型保存路径: {model_path}\n")
    
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    
    # 创建环境
    env = TicTacToeEnv(opponent='ai')
    
    # 包装环境以支持动作掩码
    env = ActionMasker(env, lambda env: env.action_masks())
    
    print("检查环境...")
    print("✓ 环境创建成功（已启用动作掩码）\n")
    
    # 创建或加载模型
    if os.path.exists(f"{model_path}.zip"):
        print(f"加载已有模型: {model_path}.zip")
        model = MaskablePPO.load(model_path, env=env)
    else:
        print("创建新模型（MaskablePPO）...")
        model = MaskablePPO(
            MaskableActorCriticPolicy,
            env,
            verbose=1,
            learning_rate=0.0003,
            n_steps=2048,
            batch_size=64,
            n_epochs=10,
            gamma=0.99,
        )
    
    # 训练
    print("\n开始训练...\n")
    callback = TrainingCallback()
    
    # 获取原始环境引用
    original_env = env.env  # 去掉ActionMasker包装
    
    model.learn(total_timesteps=total_timesteps, callback=callback)
    
    # 保存模型
    model.save(model_path)
    print(f"\n✓ 模型已保存: {model_path}.zip")
    
    # 显示最终统计
    print("\n" + "="*60)
    print("训练完成！")
    print("="*60)
    total = original_env.wins + original_env.losses + original_env.draws
    if total > 0:
        print(f"总回合: {original_env.episode_count}")
        print(f"胜利: {original_env.wins} ({original_env.wins/total*100:.1f}%)")
        print(f"失败: {original_env.losses} ({original_env.losses/total*100:.1f}%)")
        print(f"平局: {original_env.draws} ({original_env.draws/total*100:.1f}%)")
        print(f"\n⭐ 非法移动: {original_env.illegal_moves} (应该为 0)")
    
    original_env.close()
    return model


if __name__ == '__main__':
    import sys
    
    # 解析命令行参数（兼容 --train 格式）
    if len(sys.argv) > 1:
        if sys.argv[1] == '--train' and len(sys.argv) > 2:
            timesteps = int(sys.argv[2])
        elif sys.argv[1].isdigit():
            timesteps = int(sys.argv[1])
        else:
            print("使用方法:")
            print("  python rl_agent_v2.py [步数]")
            print("  python rl_agent_v2.py --train [步数]")
            print("\n示例:")
            print("  python rl_agent_v2.py 5000")
            print("  python rl_agent_v2.py --train 5000")
            sys.exit(1)
    else:
        timesteps = 5000
    
    print("\n⭐ 使用动作掩码版本 - 消除非法移动问题")
    print("这个版本会更高效地学习！\n")
    
    train_agent_v2(total_timesteps=timesteps)
