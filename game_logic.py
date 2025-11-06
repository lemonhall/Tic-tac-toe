"""
井字棋游戏核心逻辑
包含游戏规则、状态管理、胜负判定等
"""
import uuid
from typing import Optional, List, Tuple, Dict
from enum import Enum
from datetime import datetime


class PlayerType(Enum):
    """玩家类型"""
    HUMAN = "human"
    AI = "ai"
    AGENT = "agent"


class GameStatus(Enum):
    """游戏状态"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"


class TicTacToeGame:
    """井字棋游戏类"""
    
    def __init__(self, player_x_type: str = "human", player_o_type: str = "human"):
        self.game_id = str(uuid.uuid4())
        self.board = [[None for _ in range(3)] for _ in range(3)]
        self.current_player = 'X'
        self.status = GameStatus.IN_PROGRESS
        self.winner = None
        self.winning_line = None
        self.move_count = 0
        self.move_history = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
        # 玩家类型
        self.player_x_type = PlayerType(player_x_type)
        self.player_o_type = PlayerType(player_o_type)
        
    def make_move(self, row: int, col: int, player: str = None) -> Dict:
        """
        下棋
        :param row: 行号 (0-2)
        :param col: 列号 (0-2)
        :param player: 玩家标识（X或O），如果为None则使用当前玩家
        :return: 移动结果
        """
        # 验证游戏状态
        if self.status != GameStatus.IN_PROGRESS:
            return {
                "success": False,
                "error": "游戏未进行中"
            }
        
        # 使用指定的玩家或当前玩家
        if player is None:
            player = self.current_player
        elif player != self.current_player:
            return {
                "success": False,
                "error": f"当前是玩家 {self.current_player} 的回合"
            }
        
        # 验证移动合法性
        if not self.is_valid_move(row, col):
            return {
                "success": False,
                "error": "非法移动"
            }
        
        # 执行移动
        self.board[row][col] = player
        self.move_count += 1
        self.move_history.append({
            "player": player,
            "row": row,
            "col": col,
            "move_number": self.move_count,
            "timestamp": datetime.now().isoformat()
        })
        self.updated_at = datetime.now()
        
        # 检查游戏是否结束
        winner = self.check_winner()
        if winner:
            self.status = GameStatus.FINISHED
            self.winner = winner
            self.winning_line = self.get_winning_line()
            return {
                "success": True,
                "game_over": True,
                "winner": winner,
                "winning_line": self.winning_line,
                "is_draw": False
            }
        
        # 检查平局
        if self.is_board_full():
            self.status = GameStatus.FINISHED
            return {
                "success": True,
                "game_over": True,
                "winner": None,
                "winning_line": None,
                "is_draw": True
            }
        
        # 切换玩家
        self.current_player = 'O' if self.current_player == 'X' else 'X'
        
        return {
            "success": True,
            "game_over": False,
            "next_player": self.current_player
        }
    
    def is_valid_move(self, row: int, col: int) -> bool:
        """
        检查移动是否合法
        """
        if row < 0 or row > 2 or col < 0 or col > 2:
            return False
        
        if self.board[row][col] is not None:
            return False
        
        return True
    
    def check_winner(self) -> Optional[str]:
        """
        检查是否有玩家获胜
        :return: 获胜玩家（'X'或'O'），如果没有则返回None
        """
        # 检查行
        for row in self.board:
            if row[0] == row[1] == row[2] and row[0] is not None:
                return row[0]
        
        # 检查列
        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] and self.board[0][col] is not None:
                return self.board[0][col]
        
        # 检查对角线
        if self.board[0][0] == self.board[1][1] == self.board[2][2] and self.board[0][0] is not None:
            return self.board[0][0]
        
        if self.board[0][2] == self.board[1][1] == self.board[2][0] and self.board[0][2] is not None:
            return self.board[0][2]
        
        return None
    
    def get_winning_line(self) -> Optional[List[Tuple[int, int]]]:
        """
        获取获胜的连线位置
        :return: 连线的起始和结束坐标 [[row1, col1], [row2, col2]]
        """
        # 检查行
        for i, row in enumerate(self.board):
            if row[0] == row[1] == row[2] and row[0] is not None:
                return [[i, 0], [i, 2]]
        
        # 检查列
        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] and self.board[0][col] is not None:
                return [[0, col], [2, col]]
        
        # 检查对角线
        if self.board[0][0] == self.board[1][1] == self.board[2][2] and self.board[0][0] is not None:
            return [[0, 0], [2, 2]]
        
        if self.board[0][2] == self.board[1][1] == self.board[2][0] and self.board[0][2] is not None:
            return [[0, 2], [2, 0]]
        
        return None
    
    def is_board_full(self) -> bool:
        """
        检查棋盘是否已满
        """
        for row in self.board:
            if None in row:
                return False
        return True
    
    def reset(self):
        """
        重置游戏
        """
        self.board = [[None for _ in range(3)] for _ in range(3)]
        self.current_player = 'X'
        self.status = GameStatus.IN_PROGRESS
        self.winner = None
        self.winning_line = None
        self.move_count = 0
        self.move_history = []
        self.updated_at = datetime.now()
    
    def get_state(self) -> Dict:
        """
        获取当前游戏状态
        """
        return {
            "game_id": self.game_id,
            "board": self.board,
            "current_player": self.current_player,
            "status": self.status.value,
            "winner": self.winner,
            "winning_line": self.winning_line,
            "move_count": self.move_count,
            "move_history": self.move_history,
            "player_x_type": self.player_x_type.value,
            "player_o_type": self.player_o_type.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    def get_available_moves(self) -> List[Tuple[int, int]]:
        """
        获取所有可用的移动位置
        """
        moves = []
        for row in range(3):
            for col in range(3):
                if self.board[row][col] is None:
                    moves.append((row, col))
        return moves
    
    def clone(self):
        """
        克隆游戏状态（用于AI模拟）
        """
        cloned = TicTacToeGame(
            self.player_x_type.value,
            self.player_o_type.value
        )
        cloned.board = [row[:] for row in self.board]
        cloned.current_player = self.current_player
        cloned.status = self.status
        cloned.winner = self.winner
        cloned.move_count = self.move_count
        return cloned
    
    def __str__(self):
        """
        字符串表示（用于调试）
        """
        lines = []
        for row in self.board:
            line = " | ".join([cell if cell else " " for cell in row])
            lines.append(line)
        return "\n" + "-" * 9 + "\n".join(["\n" + line for line in lines]) + "\n" + "-" * 9
