"""
快速演示脚本
展示系统的主要功能
"""
import time
import sys


def print_banner():
    """打印横幅"""
    print("=" * 60)
    print(" " * 15 + "井字棋决斗场 演示")
    print(" " * 10 + "Tic-Tac-Toe Arena Demo")
    print("=" * 60)
    print()


def print_section(title):
    """打印章节标题"""
    print("\n" + "-" * 60)
    print(f"  {title}")
    print("-" * 60)


def demo_game_logic():
    """演示游戏逻辑"""
    from game_logic import TicTacToeGame
    
    print_section("1. 游戏逻辑演示")
    
    print("\n创建新游戏...")
    game = TicTacToeGame()
    print(f"✓ 游戏ID: {game.game_id}")
    print(f"✓ 当前玩家: {game.current_player}")
    print(game)
    
    print("\n下棋演示...")
    moves = [(0, 0), (1, 1), (0, 1), (2, 0), (0, 2)]
    
    for row, col in moves:
        result = game.make_move(row, col)
        print(f"\n玩家移动到 ({row}, {col})")
        print(game)
        
        if result.get("game_over"):
            if result.get("is_draw"):
                print("\n🤝 游戏结束 - 平局！")
            else:
                print(f"\n🎉 游戏结束 - 玩家 {result['winner']} 获胜！")
            break
        
        time.sleep(0.5)


def demo_simple_ai():
    """演示简单AI"""
    from game_logic import TicTacToeGame
    from ai_strategy import SimpleAI
    
    print_section("2. 简单AI演示")
    
    print("\n创建游戏: 人类 vs AI")
    game = TicTacToeGame('human', 'ai')
    ai = SimpleAI()
    
    print("人类先手...")
    game.make_move(0, 0)  # 人类下在角落
    print(game)
    
    print("\nAI思考中...")
    time.sleep(1)
    ai_move = ai.get_best_move(game)
    print(f"AI选择: {ai_move}")
    game.make_move(ai_move[0], ai_move[1])
    print(game)


def demo_minimax_ai():
    """演示Minimax AI"""
    from game_logic import TicTacToeGame
    from ai_strategy import TicTacToeAI
    
    print_section("3. Minimax AI演示")
    
    print("\n创建高级AI...")
    game = TicTacToeGame('human', 'ai')
    ai = TicTacToeAI(difficulty='hard')
    
    print("测试: AI能否找到获胜策略？")
    print("\n设置局面: O即将获胜")
    game.board = [
        ['X', 'O', 'X'],
        [None, 'O', None],
        ['X', None, None]
    ]
    game.current_player = 'O'
    print(game)
    
    print("\nAI分析中...")
    time.sleep(1)
    ai_move = ai.get_best_move(game)
    print(f"AI选择: {ai_move} (应该是 (2, 1) 以获胜)")


def demo_ai_vs_ai():
    """演示AI对战"""
    from game_logic import TicTacToeGame
    from ai_strategy import SimpleAI
    
    print_section("4. AI vs AI 演示")
    
    print("\n开始AI对战...")
    game = TicTacToeGame('ai', 'ai')
    ai = SimpleAI()
    
    move_count = 0
    while game.status.value == 'in_progress':
        move = ai.get_best_move(game)
        if move:
            current = game.current_player
            result = game.make_move(move[0], move[1])
            move_count += 1
            
            print(f"\n第 {move_count} 步: 玩家 {current} -> {move}")
            print(game)
            
            if result.get('game_over'):
                if result.get('is_draw'):
                    print("\n🤝 游戏结束 - 平局！")
                else:
                    print(f"\n🎉 游戏结束 - 玩家 {result['winner']} 获胜！")
                break
            
            time.sleep(0.5)
        else:
            break


def demo_game_manager():
    """演示游戏管理器"""
    from game_manager import game_manager
    
    print_section("5. 游戏管理器演示")
    
    print("\n创建多个游戏...")
    game1 = game_manager.create_game('human', 'ai')
    print(f"✓ 游戏1: {game1.game_id}")
    
    game2 = game_manager.create_game('ai', 'ai')
    print(f"✓ 游戏2: {game2.game_id}")
    
    print(f"\n当前活动游戏数: {len(game_manager.games)}")
    
    print("\n执行一些移动...")
    game_manager.make_move(game1.game_id, 0, 0)
    game_manager.make_move(game2.game_id, 1, 1)
    
    print(f"✓ 游戏1已下 {game1.move_count} 步")
    print(f"✓ 游戏2已下 {game2.move_count} 步")
    
    print("\n获取所有游戏状态...")
    all_games = game_manager.get_all_games()
    print(f"✓ 获取到 {len(all_games)} 个游戏")


def demo_api_endpoints():
    """演示API端点（需要服务器运行）"""
    print_section("6. API端点说明")
    
    print("\n可用的API端点:")
    print("  POST   /api/game/create         - 创建游戏")
    print("  GET    /api/game/{id}/state     - 获取状态")
    print("  POST   /api/game/{id}/move      - 下棋")
    print("  POST   /api/game/{id}/ai-move   - AI移动")
    print("  POST   /api/game/{id}/reset     - 重置游戏")
    print("  GET    /api/game/{id}/events    - SSE事件流")
    print("  GET    /api/games               - 列出所有游戏")
    print("  DELETE /api/game/{id}           - 删除游戏")
    print("  GET    /api/health              - 健康检查")
    
    print("\n要测试API，请运行:")
    print("  1. python app.py  (启动服务器)")
    print("  2. 访问 http://localhost:5000")
    print("  3. 或运行: python example_agent.py")


def main():
    """主函数"""
    print_banner()
    
    print("本演示将展示井字棋决斗场的核心功能")
    print("每个演示之间会有短暂停顿\n")
    
    try:
        # 演示1: 游戏逻辑
        input("按回车开始演示1: 游戏逻辑...")
        demo_game_logic()
        
        # 演示2: 简单AI
        input("\n按回车开始演示2: 简单AI...")
        demo_simple_ai()
        
        # 演示3: Minimax AI
        input("\n按回车开始演示3: Minimax AI...")
        demo_minimax_ai()
        
        # 演示4: AI对战
        input("\n按回车开始演示4: AI vs AI...")
        demo_ai_vs_ai()
        
        # 演示5: 游戏管理器
        input("\n按回车开始演示5: 游戏管理器...")
        demo_game_manager()
        
        # 演示6: API说明
        input("\n按回车查看演示6: API端点...")
        demo_api_endpoints()
        
        # 结束
        print("\n" + "=" * 60)
        print("  演示完成！")
        print("=" * 60)
        print("\n下一步:")
        print("  1. 运行: python app.py")
        print("  2. 访问: http://localhost:5000")
        print("  3. 查看: README.md 和 API.md")
        print("  4. 尝试: python example_agent.py")
        print("\n祝你玩得开心！ 🎮")
        
    except KeyboardInterrupt:
        print("\n\n演示已中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
