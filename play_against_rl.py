"""
让训练好的 RL Agent 作为外部玩家接入 Web 游戏
人类可以在浏览器中和 Agent 对弈
"""
import requests
import numpy as np
import time
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
import sys

class RLWebPlayer:
    """RL Agent Web 玩家"""
    
    def __init__(self, model_path='models/rl_agent_v2_ppo', base_url='http://127.0.0.1:5000'):
        self.model_path = model_path
        self.base_url = base_url
        self.session = requests.Session()
        
        # 加载模型
        print(f"🤖 加载 RL Agent: {model_path}.zip")
        self.model = MaskablePPO.load(f"{model_path}")
        print("✓ 模型加载成功\n")
    
    def board_to_observation(self, board, player):
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
    
    def get_action_masks(self, board):
        """获取动作掩码（哪些位置可以下）"""
        masks = []
        for row in board:
            for cell in row:
                masks.append(cell is None)
        return np.array(masks, dtype=np.bool_)
    
    def action_to_position(self, action):
        """将动作转换为位置"""
        return int(action // 3), int(action % 3)
    
    def play_game(self, game_id, agent_player):
        """对弈一局游戏
        
        Args:
            game_id: 游戏 ID
            agent_player: Agent 扮演的角色 ('X' 或 'O')
        """
        print(f"   连接到游戏: {game_id}")
        print(f"   Agent 扮演 {agent_player} 玩家")
        
        if agent_player == 'X':
            print("   Agent 先手！")
        else:
            print("   等待人类先手...")
        print()
        
        # 监听游戏状态
        player = agent_player
        
        while True:
            time.sleep(0.5)
            
            # 获取游戏状态
            response = self.session.get(f'{self.base_url}/api/game/{game_id}/state')
            if response.status_code != 200:
                print("   ❌ 获取游戏状态失败")
                return None
            
            game_state = response.json()['game_state']
            board = game_state['board']
            status = game_state['status']
            current_player = game_state['current_player']
            
            # 检查游戏是否结束
            if status == 'finished':
                winner = game_state.get('winner')
                if winner == player:
                    print(f"\n   🎉 Agent ({player}) 胜利!")
                    return 'win'
                elif winner is None:
                    print("\n   🤝 平局!")
                    return 'draw'
                else:
                    print(f"\n   😢 Agent ({player}) 失败...")
                    return 'loss'
            
            # 如果轮到 Agent
            if current_player == player:
                # 获取观察和动作掩码
                obs = self.board_to_observation(board, player)
                action_masks = self.get_action_masks(board)
                
                # 使用模型预测（确定性输出）
                action, _ = self.model.predict(obs, action_masks=action_masks, deterministic=True)
                row, col = self.action_to_position(action)
                
                # 下棋
                response = self.session.post(
                    f'{self.base_url}/api/game/{game_id}/move',
                    json={'row': row, 'col': col}
                )
                
                if response.status_code == 200:
                    print(f"   🤖 Agent ({player}) 下在: ({row}, {col})")
                else:
                    print(f"   ❌ 下棋失败: {response.text}")
                    return None
    
    def run_continuous(self):
        """连续对战模式 - 自动检测新游戏"""
        print("="*60)
        print("🤖 智能连续对战模式")
        print("="*60)
        print(f"\n📍 使用说明:")
        print(f"1. 在浏览器中打开: {self.base_url}")
        print(f"2. 选择玩家配置:")
        print(f"   - 外部Agent vs 人类 → Agent 先手 (X)")
        print(f"   - 人类 vs 外部Agent → Agent 后手 (O)")
        print(f"3. 点击 '开始游戏'")
        print(f"4. Agent 会自动检测并加入游戏！")
        print(f"5. 对弈结束后，点击 '再来一局'，Agent 会自动加入")
        print(f"\n🎯 支持 Agent 扮演 X 或 O，无需手动输入游戏 ID！\n")
        print(f"⏳ Agent 准备就绪，监听新游戏中...")
        print(f"   (按 Ctrl+C 退出)\n")
        print("-"*60)
        
        game_count = 0
        wins = 0
        losses = 0
        draws = 0
        processed_games = set()  # 记录已处理的游戏
        
        try:
            while True:
                time.sleep(1)  # 每秒检查一次
                
                # 获取所有进行中的游戏
                response = self.session.get(f'{self.base_url}/api/games?status=in_progress')
                if response.status_code != 200:
                    continue
                
                games = response.json().get('games', {})
                
                # 查找需要外部 Agent 且未处理的游戏
                for game_id, game_info in games.items():
                    # 跳过已处理的游戏
                    if game_id in processed_games:
                        continue
                    
                    # 检查是否需要外部 Agent（X 或 O 玩家是 agent）
                    agent_player = None
                    if game_info['player_x_type'] == 'agent':
                        agent_player = 'X'
                    elif game_info['player_o_type'] == 'agent':
                        agent_player = 'O'
                    
                    if agent_player:
                        print(f"\n🎮 发现新游戏！")
                        print(f"   游戏 ID: {game_id}")
                        print(f"   玩家配置: {game_info['player_x_type']} vs {game_info['player_o_type']}")
                        print(f"   Agent 扮演: {agent_player}")
                        
                        # 标记为已处理
                        processed_games.add(game_id)
                        game_count += 1
                        
                        print(f"\n📊 第 {game_count} 局开始...")
                        
                        # 开始对弈
                        result = self.play_game(game_id, agent_player)
                        
                        if result == 'win':
                            wins += 1
                        elif result == 'loss':
                            losses += 1
                        elif result == 'draw':
                            draws += 1
                        
                        # 显示战绩
                        print("\n" + "="*60)
                        print(f"📈 累计战绩: {game_count} 局")
                        if wins + losses + draws > 0:
                            print(f"   胜: {wins} | 负: {losses} | 平: {draws}")
                            total = wins + losses + draws
                            print(f"   胜率: {wins/total*100:.1f}% | 平局率: {draws/total*100:.1f}%")
                        print("="*60)
                        
                        print("\n💡 在浏览器中点击 '再来一局'，Agent 会自动加入新游戏！")
                        print("   等待下一局...")
                        
        except KeyboardInterrupt:
            print("\n\n" + "="*60)
            print("📊 最终战绩")
            print("="*60)
            print(f"总局数: {game_count}")
            if wins + losses + draws > 0:
                total = wins + losses + draws
                print(f"胜: {wins} ({wins/total*100:.1f}%)")
                print(f"负: {losses} ({losses/total*100:.1f}%)")
                print(f"平: {draws} ({draws/total*100:.1f}%)")
            print("="*60)
            print("\n👋 感谢对弈！")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎮 RL Agent Web 对弈模式")
    print("="*60)
    print("\n这个程序会让训练好的 RL Agent 作为玩家")
    print("你可以在浏览器中和它连续对弈多局！\n")
    
    # 检查模型文件
    import os
    model_path = 'models/rl_agent_v2_ppo'
    if not os.path.exists(f"{model_path}.zip"):
        print(f"❌ 找不到模型文件: {model_path}.zip")
        print("\n请先训练模型:")
        print("  python rl_agent_v2.py --train 5000")
        sys.exit(1)
    
    player = RLWebPlayer(model_path=model_path)
    
    try:
        player.run_continuous()
    except KeyboardInterrupt:
        print("\n\n👋 游戏中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
