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
    
    def play_game(self):
        """开始对弈 - 等待浏览器创建的游戏"""
        print("="*60)
        print("🎮 等待游戏开始...")
        print("="*60)
        print(f"\n📍 步骤:")
        print(f"1. 在浏览器中打开: {self.base_url}")
        print(f"2. 选择 '人类 vs AI' 模式")
        print(f"3. 点击 '开始游戏'")
        print(f"4. Agent 会自动接管 AI (O 玩家)")
        print(f"\n⏳ Agent 准备就绪，等待游戏创建...\n")
        print("-"*60)
        
        # 轮询等待新游戏
        last_game_count = 0
        game_id = None
        
        while True:
            time.sleep(1)
            
            # 获取所有游戏（这需要一个新的 API 端点，或者我们监听最新的游戏）
            # 简化版：让用户手动输入游戏 ID
            
            # 更好的方案：查找最新的"等待中"的游戏
            # 但这需要修改后端 API
            
            # 目前最简单的方案：让用户在创建游戏后，把 game_id 告诉 Agent
            break
        
        print("\n💡 请按以下步骤操作:")
        print("1. 在浏览器中创建 '人类 vs AI' 游戏")
        print("2. 游戏开始后，先不要下棋")
        print("3. 打开浏览器开发者工具 (F12)")
        print("4. 在 Console 中输入: gameState.gameId")
        print("5. 复制游戏 ID 并粘贴到这里\n")
        
        game_id = input("🎯 请输入游戏 ID: ").strip()
        
        if not game_id:
            print("❌ 没有输入游戏 ID")
            return
        
        print(f"\n✓ 连接到游戏: {game_id}")
        print("Agent 将扮演 O 玩家")
        print("等待人类玩家 (X) 先手...\n")
        print("-"*60)
        
        # 监听游戏状态
        player = 'O'  # Agent 是 O
        
        while True:
            time.sleep(0.5)
            
            # 获取游戏状态
            response = self.session.get(f'{self.base_url}/api/game/{game_id}/state')
            if response.status_code != 200:
                print("❌ 获取游戏状态失败，游戏 ID 可能不正确")
                break
            
            game_state = response.json()['game_state']
            board = game_state['board']
            status = game_state['status']
            current_player = game_state['current_player']
            
            # 检查游戏是否结束
            if status == 'finished':
                winner = game_state.get('winner')
                if winner == player:
                    print("\n🎉 Agent 胜利!")
                elif winner is None:
                    print("\n🤝 平局!")
                else:
                    print("\n😢 Agent 失败...")
                
                print("\n游戏结束！")
                break
            
            # 如果轮到 Agent
            if current_player == player:
                print(f"\n🤖 Agent 思考中...")
                
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
                    print(f"✓ Agent 下在: ({row}, {col})")
                    print("等待人类玩家...")
                else:
                    print(f"❌ 下棋失败: {response.text}")
                    break


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎮 RL Agent Web 对弈模式")
    print("="*60)
    print("\n这个程序会让训练好的 RL Agent 作为玩家")
    print("你可以在浏览器中和它对弈！\n")
    
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
        player.play_game()
    except KeyboardInterrupt:
        print("\n\n👋 游戏中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
