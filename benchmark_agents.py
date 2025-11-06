"""
性能对比测试
比较不同 Agent 的表现：随机 Agent vs 强化学习 Agent
"""
import requests
import random
import time
import os


class BenchmarkAgent:
    """基准测试 Agent"""
    
    def __init__(self, base_url='http://127.0.0.1:5000', name="Agent"):
        self.base_url = base_url
        self.name = name
        self.game_id = None
        self.player = None
    
    def create_game(self, player_x='agent', player_o='ai'):
        """创建游戏"""
        try:
            response = requests.post(f'{self.base_url}/api/game/create',
                                   json={'player_x_type': player_x, 'player_o_type': player_o},
                                   timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.game_id = data['game_id']
                self.player = 'X' if player_x == 'agent' else 'O'
                return True
        except:
            pass
        return False
    
    def get_state(self):
        """获取状态"""
        try:
            response = requests.get(f'{self.base_url}/api/game/{self.game_id}/state', timeout=5)
            if response.status_code == 200:
                return response.json().get('game_state')
        except:
            pass
        return None
    
    def make_move(self, row, col):
        """下棋"""
        try:
            response = requests.post(f'{self.base_url}/api/game/{self.game_id}/move',
                                    json={'row': row, 'col': col}, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def request_ai_move(self):
        """请求 AI 移动"""
        try:
            response = requests.post(f'{self.base_url}/api/game/{self.game_id}/ai-move', timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def decide_move(self, board):
        """决定移动（子类实现）"""
        raise NotImplementedError


class RandomAgent(BenchmarkAgent):
    """随机策略 Agent"""
    
    def decide_move(self, board):
        """随机选择"""
        moves = []
        for i in range(3):
            for j in range(3):
                if board[i][j] is None:
                    moves.append((i, j))
        return random.choice(moves) if moves else None


class RLAgent(BenchmarkAgent):
    """强化学习 Agent"""
    
    def __init__(self, base_url='http://127.0.0.1:5000', name="RL-Agent", model_path='models/rl_agent_ppo'):
        super().__init__(base_url, name)
        
        # 加载模型
        from stable_baselines3 import PPO
        import numpy as np
        
        self.model = PPO.load(model_path)
        self.np = np
    
    def decide_move(self, board):
        """使用模型决策"""
        # 转换棋盘为观察
        obs = []
        for row in board:
            for cell in row:
                if cell is None:
                    obs.append(0)
                elif cell == self.player:
                    obs.append(1)
                else:
                    obs.append(-1)
        
        obs = self.np.array(obs, dtype=self.np.float32)
        
        # 预测动作
        action, _ = self.model.predict(obs, deterministic=True)
        row, col = action // 3, action % 3
        
        # 检查合法性
        if board[row][col] is None:
            return (row, col)
        
        # 如果非法，随机选择
        moves = []
        for i in range(3):
            for j in range(3):
                if board[i][j] is None:
                    moves.append((i, j))
        return random.choice(moves) if moves else None


def play_one_game(agent):
    """玩一局游戏"""
    if not agent.create_game('agent', 'ai'):
        return None
    
    while True:
        state = agent.get_state()
        if not state:
            return None
        
        if state['status'] == 'finished':
            winner = state.get('winner')
            if winner == agent.player:
                return 'win'
            elif winner is None:
                return 'draw'
            else:
                return 'loss'
        
        current_player = state['current_player']
        if current_player == agent.player:
            board = state['board']
            move = agent.decide_move(board)
            if move:
                agent.make_move(move[0], move[1])
                time.sleep(0.05)
            else:
                return 'error'
        else:
            agent.request_ai_move()
            time.sleep(0.05)


def benchmark(agent_class, agent_kwargs, num_games=50):
    """性能基准测试"""
    print(f"\n{'='*60}")
    print(f"测试 {agent_kwargs['name']}")
    print(f"{'='*60}")
    print(f"对局数: {num_games}\n")
    
    wins = 0
    losses = 0
    draws = 0
    errors = 0
    
    start_time = time.time()
    
    for i in range(num_games):
        agent = agent_class(**agent_kwargs)
        result = play_one_game(agent)
        
        if result == 'win':
            wins += 1
            status = '✓'
        elif result == 'loss':
            losses += 1
            status = '✗'
        elif result == 'draw':
            draws += 1
            status = '-'
        else:
            errors += 1
            status = '!'
        
        print(f"[{i+1:3d}/{num_games}] {status} ", end='', flush=True)
        
        if (i + 1) % 10 == 0:
            print()
        
        time.sleep(0.5)
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    print(f"\n\n{'='*60}")
    print("测试结果")
    print(f"{'='*60}")
    print(f"总耗时: {elapsed:.1f}秒")
    print(f"平均每局: {elapsed/num_games:.2f}秒")
    print(f"\n胜利: {wins} ({wins/num_games*100:.1f}%)")
    print(f"失败: {losses} ({losses/num_games*100:.1f}%)")
    print(f"平局: {draws} ({draws/num_games*100:.1f}%)")
    if errors > 0:
        print(f"错误: {errors}")
    print(f"{'='*60}\n")
    
    return {
        'wins': wins,
        'losses': losses,
        'draws': draws,
        'errors': errors,
        'total': num_games,
        'win_rate': wins / num_games,
        'elapsed': elapsed
    }


def compare_agents(num_games=50):
    """比较不同 Agent"""
    print("\n" + "="*60)
    print("Agent 性能对比测试")
    print("="*60)
    print(f"每个 Agent 将对战 {num_games} 局")
    print("对手: 内置 AI")
    print("="*60)
    
    results = {}
    
    # 测试随机 Agent
    print("\n【1/2】测试随机策略 Agent")
    results['random'] = benchmark(
        RandomAgent,
        {'base_url': 'http://127.0.0.1:5000', 'name': '随机Agent'},
        num_games
    )
    
    # 测试强化学习 Agent
    print("\n【2/2】测试强化学习 Agent")
    
    model_path = 'models/rl_agent_ppo'
    if not os.path.exists(f"{model_path}.zip"):
        print(f"✗ 模型不存在: {model_path}.zip")
        print("请先训练模型: python rl_agent.py --train 5000")
        return
    
    results['rl'] = benchmark(
        RLAgent,
        {'base_url': 'http://127.0.0.1:5000', 'name': '强化学习Agent', 'model_path': model_path},
        num_games
    )
    
    # 对比总结
    print("\n" + "="*60)
    print("对比总结")
    print("="*60)
    print(f"\n{'Agent':<20} {'胜率':<10} {'平均耗时':<15}")
    print("-"*60)
    
    for name, result in results.items():
        agent_name = "随机Agent" if name == 'random' else "强化学习Agent"
        win_rate = f"{result['win_rate']*100:.1f}%"
        avg_time = f"{result['elapsed']/result['total']:.2f}秒"
        print(f"{agent_name:<20} {win_rate:<10} {avg_time:<15}")
    
    if 'random' in results and 'rl' in results:
        improvement = (results['rl']['win_rate'] - results['random']['win_rate']) * 100
        print(f"\n强化学习相比随机策略提升: {improvement:+.1f}%")
    
    print("="*60)


if __name__ == '__main__':
    import sys
    
    num_games = 50
    if len(sys.argv) > 1:
        try:
            num_games = int(sys.argv[1])
        except:
            pass
    
    print("\n性能对比测试")
    print("="*60)
    print("确保服务器正在运行: python app.py")
    print(f"将进行 {num_games} 局对战")
    print("="*60)
    
    input("\n按 Enter 开始测试...")
    
    compare_agents(num_games)
    
    print("\n测试完成！")
