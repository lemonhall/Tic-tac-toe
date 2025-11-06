"""
AI策略实现
使用Minimax算法实现的简单AI
"""
from typing import Tuple, Optional
import random


class TicTacToeAI:
    """井字棋AI"""
    
    def __init__(self, difficulty: str = "hard"):
        """
        :param difficulty: 难度级别 - "easy", "medium", "hard"
        """
        self.difficulty = difficulty
    
    def get_best_move(self, game) -> Optional[Tuple[int, int]]:
        """
        获取最佳移动
        :param game: 游戏实例
        :return: (row, col) 或 None
        """
        if self.difficulty == "easy":
            return self._get_random_move(game)
        elif self.difficulty == "medium":
            # 中等难度：50%使用最佳策略，50%随机
            if random.random() < 0.5:
                return self._get_minimax_move(game)
            else:
                return self._get_random_move(game)
        else:  # hard
            return self._get_minimax_move(game)
    
    def _get_random_move(self, game) -> Optional[Tuple[int, int]]:
        """
        获取随机移动（简单难度）
        """
        available_moves = game.get_available_moves()
        if not available_moves:
            return None
        return random.choice(available_moves)
    
    def _get_minimax_move(self, game) -> Optional[Tuple[int, int]]:
        """
        使用Minimax算法获取最佳移动
        """
        available_moves = game.get_available_moves()
        if not available_moves:
            return None
        
        # 如果是第一步，选择中心或角落（优化性能）
        if game.move_count == 0:
            # 优先选择中心
            return (1, 1)
        
        if game.move_count == 1:
            # 如果中心被占，选择角落
            if game.board[1][1] is not None:
                corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
                return random.choice(corners)
            else:
                return (1, 1)
        
        best_score = float('-inf')
        best_move = None
        alpha = float('-inf')
        beta = float('inf')
        
        # 评估每个可能的移动
        for row, col in available_moves:
            # 模拟移动
            cloned_game = game.clone()
            cloned_game.board[row][col] = game.current_player
            
            # 使用Minimax评估
            score = self._minimax(cloned_game, 0, False, alpha, beta)
            
            # 更新最佳移动
            if score > best_score:
                best_score = score
                best_move = (row, col)
            
            alpha = max(alpha, score)
        
        return best_move
    
    def _minimax(self, game, depth: int, is_maximizing: bool, alpha: float, beta: float) -> float:
        """
        Minimax算法实现（带Alpha-Beta剪枝）
        :param game: 游戏状态
        :param depth: 当前深度
        :param is_maximizing: 是否是最大化玩家
        :param alpha: Alpha值
        :param beta: Beta值
        :return: 评估分数
        """
        # 检查终止条件
        winner = game.check_winner()
        if winner == game.current_player:
            return 10 - depth  # 越快获胜越好
        elif winner is not None:
            return depth - 10  # 越晚输越好
        elif game.is_board_full():
            return 0  # 平局
        
        available_moves = game.get_available_moves()
        
        if is_maximizing:
            max_score = float('-inf')
            for row, col in available_moves:
                cloned_game = game.clone()
                cloned_game.board[row][col] = game.current_player
                score = self._minimax(cloned_game, depth + 1, False, alpha, beta)
                max_score = max(max_score, score)
                alpha = max(alpha, score)
                if beta <= alpha:
                    break  # Beta剪枝
            return max_score
        else:
            min_score = float('inf')
            opponent = 'O' if game.current_player == 'X' else 'X'
            for row, col in available_moves:
                cloned_game = game.clone()
                cloned_game.board[row][col] = opponent
                cloned_game.current_player = opponent
                score = self._minimax(cloned_game, depth + 1, True, alpha, beta)
                min_score = min(min_score, score)
                beta = min(beta, score)
                if beta <= alpha:
                    break  # Alpha剪枝
            return min_score
    
    def evaluate_position(self, game) -> float:
        """
        评估当前局面
        :return: 评估分数（正数对AI有利，负数对对手有利）
        """
        winner = game.check_winner()
        if winner == game.current_player:
            return 1.0
        elif winner is not None:
            return -1.0
        else:
            return 0.0


class SimpleAI:
    """
    简化的AI实现，使用基于规则的策略
    适合作为默认AI
    """
    
    def get_best_move(self, game) -> Optional[Tuple[int, int]]:
        """
        获取最佳移动
        策略优先级：
        1. 如果能赢，立即获胜
        2. 如果对手能赢，立即阻止
        3. 占据中心
        4. 占据角落
        5. 占据边缘
        """
        available_moves = game.get_available_moves()
        if not available_moves:
            return None
        
        current_player = game.current_player
        opponent = 'O' if current_player == 'X' else 'X'
        
        # 1. 检查是否能获胜
        winning_move = self._find_winning_move(game, current_player)
        if winning_move:
            return winning_move
        
        # 2. 检查是否需要阻止对手获胜
        blocking_move = self._find_winning_move(game, opponent)
        if blocking_move:
            return blocking_move
        
        # 3. 占据中心
        if game.board[1][1] is None:
            return (1, 1)
        
        # 4. 占据角落
        corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
        available_corners = [pos for pos in corners if game.board[pos[0]][pos[1]] is None]
        if available_corners:
            return random.choice(available_corners)
        
        # 5. 占据边缘
        edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
        available_edges = [pos for pos in edges if game.board[pos[0]][pos[1]] is None]
        if available_edges:
            return random.choice(available_edges)
        
        # 随机选择
        return random.choice(available_moves)
    
    def _find_winning_move(self, game, player: str) -> Optional[Tuple[int, int]]:
        """
        查找能让指定玩家获胜的移动
        """
        for row, col in game.get_available_moves():
            # 模拟移动
            cloned_game = game.clone()
            cloned_game.board[row][col] = player
            
            # 检查是否获胜
            if cloned_game.check_winner() == player:
                return (row, col)
        
        return None
