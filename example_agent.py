"""
外部Agent接入示例
演示如何通过API接入井字棋决斗场
"""
import requests
import json
import sseclient
import random
import time


class ExampleAgent:
    """示例Agent - 随机策略"""
    
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.game_id = None
        self.player = None  # 'X' or 'O'
        
    def create_game(self, player_x='agent', player_o='ai'):
        """创建游戏"""
        url = f'{self.base_url}/api/game/create'
        response = requests.post(url, json={
            'player_x_type': player_x,
            'player_o_type': player_o
        })
        
        if response.status_code == 200:
            data = response.json()
            self.game_id = data['game_id']
            print(f"✓ 游戏创建成功: {self.game_id}")
            
            # 确定自己是哪个玩家
            if player_x == 'agent':
                self.player = 'X'
            elif player_o == 'agent':
                self.player = 'O'
            
            return True
        else:
            print(f"✗ 创建游戏失败: {response.text}")
            return False
    
    def get_available_moves(self, board):
        """获取可用的移动"""
        moves = []
        for i in range(3):
            for j in range(3):
                if board[i][j] is None:
                    moves.append((i, j))
        return moves
    
    def decide_move(self, board):
        """决定下一步移动（随机策略）"""
        available = self.get_available_moves(board)
        if available:
            return random.choice(available)
        return None
    
    def make_move(self, row, col):
        """执行移动"""
        url = f'{self.base_url}/api/game/{self.game_id}/move'
        response = requests.post(url, json={
            'row': row,
            'col': col
        })
        
        if response.status_code == 200:
            print(f"✓ Agent移动: ({row}, {col})")
            return True
        else:
            print(f"✗ 移动失败: {response.text}")
            return False
    
    def request_ai_move(self):
        """请求对方AI下棋"""
        url = f'{self.base_url}/api/game/{self.game_id}/ai-move'
        response = requests.post(url)
        
        if response.status_code == 200:
            print(f"✓ 已请求AI移动")
            return True
        else:
            print(f"✗ 请求AI移动失败: {response.text}")
            return False
    
    def listen_and_play(self):
        """监听游戏事件并自动下棋"""
        url = f'{self.base_url}/api/game/{self.game_id}/events'
        
        print(f"开始监听游戏事件...")
        print(f"我是玩家: {self.player}")
        
        try:
            response = requests.get(url, stream=True, timeout=None)
            client = sseclient.SSEClient(response)
            
            for event in client.events():
                if event.data:
                    try:
                        data = json.loads(event.data)
                        self.handle_event(data)
                    except json.JSONDecodeError:
                        pass
                        
        except KeyboardInterrupt:
            print("\n游戏中断")
        except Exception as e:
            print(f"错误: {e}")
    
    def handle_event(self, event):
        """处理游戏事件"""
        event_type = event.get('type')
        
        if event_type == 'connected':
            print("✓ SSE连接已建立")
            
        elif event_type == 'state_update':
            game_state = event.get('game_state', {})
            current_player = game_state.get('current_player')
            
            # 如果轮到我，下棋
            if current_player == self.player:
                time.sleep(0.5)  # 模拟思考时间
                board = game_state.get('board')
                move = self.decide_move(board)
                if move:
                    self.make_move(move[0], move[1])
                    
        elif event_type == 'move':
            player = event.get('player')
            row = event.get('row')
            col = event.get('col')
            next_player = event.get('next_player')
            
            print(f"📍 玩家 {player} 移动到 ({row}, {col})")
            
            # 获取游戏状态，检查下一个玩家的类型
            game_state = self.get_game_state()
            if game_state:
                player_x_type = game_state.get('player_x_type')
                player_o_type = game_state.get('player_o_type')
                
                # 判断下一个玩家的类型
                next_player_type = player_x_type if next_player == 'X' else player_o_type
                
                # 如果下一个玩家是AI，请求AI移动
                if next_player_type == 'ai':
                    print(f"🤖 下一个是AI玩家，请求AI移动...")
                    self.request_ai_move()
                # 如果下一个是我，准备下棋
                elif next_player == self.player:
                    time.sleep(0.5)  # 模拟思考
                    board = game_state.get('board')
                    move = self.decide_move(board)
                    if move:
                        self.make_move(move[0], move[1])
                        
        elif event_type == 'game_over':
            winner = event.get('winner')
            is_draw = event.get('is_draw', False)
            
            if is_draw:
                print("🤝 游戏结束 - 平局！")
            elif winner == self.player:
                print(f"🎉 游戏结束 - 我赢了！")
            else:
                print(f"😢 游戏结束 - 玩家 {winner} 获胜")
                
        elif event_type == 'error':
            print(f"❌ 错误: {event.get('message')}")
    
    def get_game_state(self):
        """获取游戏状态"""
        url = f'{self.base_url}/api/game/{self.game_id}/state'
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get('game_state')
        return None


def main():
    """主函数"""
    print("="*50)
    print("井字棋决斗场 - Agent接入示例")
    print("="*50)
    
    # 创建Agent
    agent = ExampleAgent()
    
    # 选择对手类型
    print("\n选择对手:")
    print("1. AI")
    print("2. 另一个Agent")
    print("3. 人类")
    
    choice = input("请选择 (1-3): ").strip()
    
    opponent_map = {
        '1': 'ai',
        '2': 'agent',
        '3': 'human'
    }
    
    opponent = opponent_map.get(choice, 'ai')
    
    # 选择先后手
    print("\n选择先后手:")
    print("1. 我先手 (X)")
    print("2. 对手先手 (O)")
    
    order = input("请选择 (1-2): ").strip()
    
    if order == '1':
        player_x = 'agent'
        player_o = opponent
    else:
        player_x = opponent
        player_o = 'agent'
    
    # 创建游戏
    if agent.create_game(player_x, player_o):
        print(f"\n游戏开始！访问 http://localhost:5000 查看游戏界面")
        print("按 Ctrl+C 退出\n")
        
        # 开始游戏循环
        agent.listen_and_play()


if __name__ == '__main__':
    main()
