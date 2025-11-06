"""
测试脚本 - 测试游戏逻辑和AI
"""
from game_logic import TicTacToeGame
from ai_strategy import SimpleAI, TicTacToeAI


def test_game_logic():
    """测试游戏逻辑"""
    print("="*50)
    print("测试游戏逻辑")
    print("="*50)
    
    game = TicTacToeGame()
    
    # 测试移动
    print("\n1. 测试合法移动")
    result = game.make_move(0, 0)
    print(f"移动到(0,0): {result}")
    print(game)
    
    # 测试非法移动
    print("\n2. 测试非法移动（重复位置）")
    result = game.make_move(0, 0)
    print(f"再次移动到(0,0): {result}")
    
    # 测试获胜
    print("\n3. 测试获胜检测")
    game.reset()
    game.make_move(0, 0)  # X
    game.make_move(1, 0)  # O
    game.make_move(0, 1)  # X
    game.make_move(1, 1)  # O
    result = game.make_move(0, 2)  # X 获胜
    print(f"X连成一线: {result}")
    print(game)
    
    # 测试平局
    print("\n4. 测试平局")
    game.reset()
    moves = [(0,0), (0,1), (0,2), (1,1), (1,0), (1,2), (2,1), (2,0), (2,2)]
    for i, (row, col) in enumerate(moves):
        result = game.make_move(row, col)
        if i == len(moves) - 1:
            print(f"最后一步: {result}")
    print(game)
    
    print("\n✓ 游戏逻辑测试完成")


def test_ai():
    """测试AI"""
    print("\n" + "="*50)
    print("测试AI策略")
    print("="*50)
    
    # 测试SimpleAI
    print("\n1. 测试SimpleAI")
    game = TicTacToeGame('human', 'ai')
    ai = SimpleAI()
    
    game.make_move(0, 0)  # X
    print(game)
    
    move = ai.get_best_move(game)
    print(f"AI选择: {move}")
    
    # 测试AI阻止获胜
    print("\n2. 测试AI防守")
    game.reset()
    game.make_move(0, 0)  # X
    game.make_move(1, 1)  # O
    game.make_move(0, 1)  # X
    print("当前局面:")
    print(game)
    
    move = ai.get_best_move(game)
    print(f"AI应该阻止X获胜，选择: {move}")
    print(f"预期: (0, 2)")
    
    # 测试AI获胜
    print("\n3. 测试AI进攻")
    game.reset()
    game.make_move(0, 0)  # X
    game.make_move(1, 0)  # O
    game.make_move(2, 2)  # X
    game.make_move(1, 1)  # O
    print("当前局面:")
    print(game)
    
    move = ai.get_best_move(game)
    print(f"AI应该立即获胜，选择: {move}")
    print(f"预期: (1, 2)")
    
    print("\n✓ AI测试完成")


def test_ai_vs_ai():
    """测试AI对战"""
    print("\n" + "="*50)
    print("测试AI vs AI")
    print("="*50)
    
    game = TicTacToeGame('ai', 'ai')
    ai = SimpleAI()
    
    move_count = 0
    while game.status.value == 'in_progress':
        move = ai.get_best_move(game)
        if move:
            result = game.make_move(move[0], move[1])
            move_count += 1
            print(f"\n第{move_count}步: 玩家{game.current_player if not result.get('game_over') else ('O' if game.current_player == 'X' else 'X')} -> {move}")
            print(game)
            
            if result.get('game_over'):
                if result.get('is_draw'):
                    print("\n游戏结束 - 平局！")
                else:
                    print(f"\n游戏结束 - 玩家 {result['winner']} 获胜！")
                break
        else:
            break
    
    print("\n✓ AI对战测试完成")


def test_minimax_ai():
    """测试Minimax AI"""
    print("\n" + "="*50)
    print("测试Minimax AI")
    print("="*50)
    
    game = TicTacToeGame('human', 'ai')
    ai = TicTacToeAI(difficulty='hard')
    
    # 测试第一步
    print("\n1. 测试第一步（应该选择中心）")
    move = ai.get_best_move(game)
    print(f"Minimax AI选择: {move}")
    print(f"预期: (1, 1)")
    
    # 测试复杂局面
    print("\n2. 测试复杂局面")
    game.reset()
    game.make_move(0, 0)  # X
    game.make_move(1, 1)  # O
    game.make_move(2, 2)  # X
    print(game)
    
    move = ai.get_best_move(game)
    print(f"Minimax AI选择: {move}")
    
    print("\n✓ Minimax AI测试完成")


if __name__ == '__main__':
    print("井字棋决斗场 - 测试套件\n")
    
    test_game_logic()
    test_ai()
    test_minimax_ai()
    test_ai_vs_ai()
    
    print("\n" + "="*50)
    print("所有测试完成！")
    print("="*50)
