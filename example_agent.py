"""
外部Agent接入示例
演示如何通过API接入井字棋决斗场
"""
import requests
import json
import sseclient
import random
import time
import threading


class ExampleAgent:
    """示例Agent - 随机策略"""
    
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.game_id = None
        self.player = None  # 'X' or 'O'
        self.game_active = False  # 游戏是否进行中
        self.timer = None  # 定时器对象
        
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
            data = response.json()
            print(f"✓ Agent移动: ({row}, {col})")
            
            # 下完棋后立即检查下一个玩家是否是AI
            if data.get('game_state'):
                game_state = data.get('game_state')
                current_player = game_state.get('current_player')
                player_x_type = game_state.get('player_x_type')
                player_o_type = game_state.get('player_o_type')
                current_player_type = player_x_type if current_player == 'X' else player_o_type
                
                # 如果现在轮到AI了，立即请求AI移动
                if current_player_type == 'ai':
                    print(f"🤖 现在轮到AI，请求AI移动...")
                    self.request_ai_move()
            
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
            data = response.json()
            
            # 检查是否是游戏已结束
            if data.get('game_over'):
                print(f"🎉 [AI请求反馈] 游戏已结束")
                winner = data.get('winner')
                is_draw = data.get('is_draw')
                
                if is_draw:
                    print(f"🎉 [AI请求反馈] 游戏结束 - 平局！")
                elif winner == self.player:
                    print(f"🎉 [AI请求反馈] 游戏结束 - 我赢了！")
                else:
                    print(f"🎉 [AI请求反馈] 游戏结束 - 玩家 {winner} 获胜")
                
                # 游戏结束，停止定时器
                self.game_active = False
                if self.timer:
                    self.timer.cancel()
                
                # 2秒后开始新游戏
                print("\n⏳ 2秒后自动开始下一局...")
                time.sleep(2)
                self.start_new_game()
                return False
            else:
                print(f"✗ 请求AI移动失败: {response.text}")
                return False
    
    def check_and_move(self):
        """定时检查是否该自己下棋"""
        if not self.game_active:
            return
        
        try:
            game_state = self.get_game_state()
            if game_state:
                # 首先检查游戏是否已结束
                status = game_state.get('status')
                if status == 'finished':
                    print(f"🎉 [定时检查] 游戏已结束，停止检查")
                    self.game_active = False
                    if self.timer:
                        self.timer.cancel()
                    
                    # 显示游戏结果
                    winner = game_state.get('winner')
                    is_draw = game_state.get('is_draw')
                    
                    if is_draw:
                        print(f"🎉 [定时检查] 游戏结束 - 平局！")
                    elif winner == self.player:
                        print(f"🎉 [定时检查] 游戏结束 - 我赢了！")
                    else:
                        print(f"🎉 [定时检查] 游戏结束 - 玩家 {winner} 获胜")
                    
                    # 2秒后开始新游戏
                    print("\n⏳ 2秒后自动开始下一局...")
                    time.sleep(2)
                    self.start_new_game()
                    return
                
                current_player = game_state.get('current_player')
                if current_player == self.player:
                    print(f"🤖 [定时检查] 轮到我了，准备下棋...")
                    time.sleep(0.5)
                    board = game_state.get('board')
                    move = self.decide_move(board)
                    if move:
                        self.make_move(move[0], move[1])
        except Exception as e:
            print(f"❌ [定时检查] 出错: {e}")
        
        # 重新设置定时器，2秒后再检查
        if self.game_active:
            self.timer = threading.Timer(2.0, self.check_and_move)
            self.timer.daemon = True
            self.timer.start()
    
    def start_game(self):
        """启动游戏 - 首先尝试下一步（如果是先手），然后监听事件"""
        # 确保之前的定时器已停止
        if self.timer:
            self.timer.cancel()
            self.timer = None
        
        print(f"我是玩家: {self.player}")
        
        # 先检查一下是否该自己下棋
        game_state = self.get_game_state()
        if game_state:
            current_player = game_state.get('current_player')
            if current_player == self.player:
                print(f"🤖 游戏开始，轮到我了，准备下棋...")
                time.sleep(0.5)
                board = game_state.get('board')
                move = self.decide_move(board)
                if move:
                    self.make_move(move[0], move[1])
        
        # 启动定时检查（每2秒检查一次）
        self.game_active = True
        self.check_and_move()
        
        # 然后开始监听事件（不再做任何主动下棋）
        self.listen_events()
    
    def listen_events(self):
        """纯粹监听游戏事件 - 不做任何HTTP请求"""
        url = f'{self.base_url}/api/game/{self.game_id}/events'
        
        print(f"开始监听游戏事件...")
        
        try:
            response = requests.get(url, stream=True, timeout=None)
            client = sseclient.SSEClient(response)
            
            for event in client.events():
                if event.data:
                    try:
                        data = json.loads(event.data)
                        self.handle_event(data)
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON解析错误: {e}")
                    except Exception as e:
                        print(f"❌ 处理事件出错: {e}")
                        
        except KeyboardInterrupt:
            print("\n游戏中断")
            self.game_active = False
            if self.timer:
                self.timer.cancel()
        except Exception as e:
            print(f"❌ SSE错误: {e}")
            self.game_active = False
            if self.timer:
                self.timer.cancel()
    
    def handle_event(self, event):
        """处理游戏事件 - 纯粹打印，不做任何HTTP请求"""
        event_type = event.get('type')
        
        if event_type == 'connected':
            print("🔔 SSE连接已建立")
            
        elif event_type == 'state_update':
            print("🔔 收到状态更新事件")
                    
        elif event_type == 'move':
            player = event.get('player')
            row = event.get('row')
            col = event.get('col')
            next_player = event.get('next_player')
            
            print(f"🔔 SSE事件: 玩家 {player} 移动到 ({row}, {col})")
            
            # 只打印，不处理逻辑
                        
        elif event_type == 'game_over':
            winner = event.get('winner')
            is_draw = event.get('is_draw', False)
            
            # 游戏结束，停止定时器
            self.game_active = False
            if self.timer:
                self.timer.cancel()
            
            if is_draw:
                print("🎉 SSE事件: 游戏结束 - 平局！")
            elif winner == self.player:
                print(f"🎉 SSE事件: 游戏结束 - 我赢了！")
            else:
                print(f"🎉 SSE事件: 游戏结束 - 玩家 {winner} 获胜")
            
            # 等待2秒后自动开始下一局
            print("\n⏳ 2秒后自动开始下一局...")
            time.sleep(2)
            self.start_new_game()
        
        elif event_type == 'game_created':
            # 游戏创建事件 - 通常在连接时发送，可以记录
            print(f"✓ 游戏已创建: {event.get('game_id')}")
        
        elif event_type == 'game_deleted':
            # 游戏被删除事件 - 游戏已过期或被清理
            print("⚠️  游戏已被删除（可能是超时）")
            self.game_active = False
            if self.timer:
                self.timer.cancel()
            # 等待后自动开始新游戏
            print("\n⏳ 2秒后自动开始新游戏...")
            time.sleep(2)
            self.start_new_game()
        
        elif event_type == 'error':
            # 错误事件
            message = event.get('message', '未知错误')
            print(f"❌ SSE错误: {message}")
        
        else:
            print(f"⚠️  未知事件类型: {event_type}")
    
    def start_new_game(self):
        """开始新一局游戏"""
        print("\n" + "="*50)
        print("🆕 开始新一局游戏")
        print("="*50 + "\n")
        
        # 确保之前的定时器已停止
        self.game_active = False
        if self.timer:
            self.timer.cancel()
            self.timer = None
        
        # 创建新游戏
        if self.create_game('agent', 'ai'):
            # 启动游戏
            self.start_game()
    
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
    
    # 自动选择：AI对手 + 先手(X)
    player_x = 'agent'
    player_o = 'ai'
    
    print(f"\n自动配置:")
    print(f"✓ 对手: AI")
    print(f"✓ 玩家: X (先手)")
    print(f"✓ 对手: O")
    
    # 创建游戏
    if agent.create_game(player_x, player_o):
        print(f"\n游戏开始！访问 http://localhost:5000 查看游戏界面")
        print("按 Ctrl+C 退出\n")
        
        # 启动游戏：先下一步，再监听事件
        agent.start_game()


if __name__ == '__main__':
    main()
