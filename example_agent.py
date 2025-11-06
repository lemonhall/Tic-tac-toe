"""
外部Agent接入示例 - 纯轮询版本
演示如何通过API接入井字棋决斗场，无线程，无复杂度
"""
import requests
import random
import time


class ExampleAgent:
    """示例Agent - 随机策略，纯同步轮询"""
    
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.game_id = None
        self.player = None  # 'X' or 'O'
    
    def create_game(self, player_x='agent', player_o='ai'):
        """创建游戏"""
        url = f'{self.base_url}/api/game/create'
        try:
            response = requests.post(url, json={
                'player_x_type': player_x,
                'player_o_type': player_o
            }, timeout=5)
            
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
        except Exception as e:
            print(f"✗ 创建游戏异常: {e}")
            return False
    
    def get_game_state(self):
        """获取游戏状态"""
        if not self.game_id:
            return None
        
        url = f'{self.base_url}/api/game/{self.game_id}/state'
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.json().get('game_state')
            return None
        except Exception as e:
            print(f"✗ 获取游戏状态异常: {e}")
            return None
    
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
        if not self.game_id:
            return False
        
        url = f'{self.base_url}/api/game/{self.game_id}/move'
        try:
            response = requests.post(url, json={
                'row': row,
                'col': col
            }, timeout=5)
            
            if response.status_code == 200:
                print(f"✓ Agent移动: ({row}, {col})")
                return True
            else:
                print(f"✗ 移动失败: {response.json().get('message', '未知错误')}")
                return False
        except Exception as e:
            print(f"✗ 移动异常: {e}")
            return False
    
    def request_ai_move(self):
        """请求AI下棋"""
        if not self.game_id:
            return False
        
        url = f'{self.base_url}/api/game/{self.game_id}/ai-move'
        try:
            response = requests.post(url, timeout=5)
            
            if response.status_code == 200:
                print(f"✓ AI已移动")
                return True
            else:
                # AI移动失败或游戏已结束
                data = response.json()
                if data.get('game_over'):
                    print(f"🎉 [AI反馈] 游戏已结束")
                    return True  # 这是正常情况（游戏结束）
                else:
                    print(f"✗ AI移动失败: {data.get('message', '未知错误')}")
                    return False
        except Exception as e:
            print(f"✗ AI移动异常: {e}")
            return False
    
    def play_one_game(self):
        """玩一局游戏 - 纯轮询"""
        print(f"\n我是玩家: {self.player}")
        
        while True:
            # 获取当前状态
            game_state = self.get_game_state()
            if not game_state:
                print("✗ 无法获取游戏状态，中止本局")
                break
            
            status = game_state.get('status')
            
            # 检查游戏是否已结束
            if status == 'finished':
                winner = game_state.get('winner')
                is_draw = game_state.get('is_draw')
                
                if is_draw:
                    print(f"🎉 游戏结束 - 平局！")
                elif winner == self.player:
                    print(f"🎉 游戏结束 - 我赢了！")
                else:
                    print(f"🎉 游戏结束 - 玩家 {winner} 获胜")
                break
            
            # 检查是否轮到我
            current_player = game_state.get('current_player')
            if current_player == self.player:
                print(f"🤖 轮到我了，准备下棋...")
                time.sleep(0.3)
                board = game_state.get('board')
                move = self.decide_move(board)
                if move:
                    self.make_move(move[0], move[1])
                    time.sleep(0.5)  # 下棋后稍等一下，让AI响应
                else:
                    print("✗ 无可用移动")
                    break
            else:
                # 轮到AI，请求AI下棋
                print(f"🤖 轮到对手，请求AI移动...")
                self.request_ai_move()
                time.sleep(0.5)  # 等待AI响应
                continue
            
            # 每轮休眠一下，避免CPU占用
            time.sleep(0.2)


def main():
    """主函数 - 持续玩游戏"""
    print("="*50)
    print("井字棋决斗场 - Agent接入示例")
    print("="*50)
    print(f"\n配置: 对手=AI, 玩家=X(先手)")
    print(f"访问 http://localhost:5000 查看游戏界面")
    print("按 Ctrl+C 退出\n")
    
    agent = ExampleAgent()
    game_count = 0
    
    try:
        while True:
            game_count += 1
            
            # 打印分隔符
            print("\n" + "="*50)
            print(f"🆕 开始第 {game_count} 局游戏")
            print("="*50)
            
            # 创建新游戏
            if agent.create_game('agent', 'ai'):
                # 玩这一局
                agent.play_one_game()
                
                # 等待2秒后开始下一局
                print("\n⏳ 2秒后自动开始下一局...")
                time.sleep(2)
            else:
                print("✗ 创建游戏失败，退出")
                break
    
    except KeyboardInterrupt:
        print(f"\n\n👋 程序已退出 (共玩了 {game_count} 局)")


if __name__ == '__main__':
    main()

