"""
游戏管理器
管理多个游戏实例
"""
from typing import Dict, Optional
from game_logic import TicTacToeGame, GameStatus
import logging

logger = logging.getLogger(__name__)


class GameManager:
    """游戏管理器"""
    
    def __init__(self):
        self.games: Dict[str, TicTacToeGame] = {}
        self.event_queues: Dict[str, list] = {}  # 存储每个游戏的事件队列
    
    def create_game(self, player_x_type: str = "human", player_o_type: str = "human") -> TicTacToeGame:
        """
        创建新游戏
        """
        game = TicTacToeGame(player_x_type, player_o_type)
        self.games[game.game_id] = game
        self.event_queues[game.game_id] = []
        
        logger.info(f"创建游戏: {game.game_id}, X类型: {player_x_type}, O类型: {player_o_type}")
        
        # 发送游戏创建事件
        self._add_event(game.game_id, {
            "type": "game_created",
            "game_id": game.game_id,
            "game_state": game.get_state()
        })
        
        return game
    
    def get_game(self, game_id: str) -> Optional[TicTacToeGame]:
        """
        获取游戏实例
        """
        return self.games.get(game_id)
    
    def make_move(self, game_id: str, row: int, col: int, player: str = None) -> Dict:
        """
        在指定游戏中下棋
        """
        game = self.get_game(game_id)
        if not game:
            return {
                "status": "error",
                "message": "游戏不存在"
            }
        
        result = game.make_move(row, col, player)
        
        if result["success"]:
            # 发送移动事件
            self._add_event(game_id, {
                "type": "move",
                "game_id": game_id,
                "row": row,
                "col": col,
                "player": player or game.current_player if result.get("game_over") else 
                         ('O' if game.current_player == 'X' else 'X'),
                "move_number": game.move_count,
                "next_player": result.get("next_player")
            })
            
            # 如果游戏结束，发送游戏结束事件
            if result.get("game_over"):
                self._add_event(game_id, {
                    "type": "game_over",
                    "game_id": game_id,
                    "winner": result.get("winner"),
                    "winning_line": result.get("winning_line"),
                    "is_draw": result.get("is_draw", False)
                })
            
            return {
                "status": "success",
                "message": "移动成功",
                "result": result,
                "game_state": game.get_state()
            }
        else:
            return {
                "status": "error",
                "message": result.get("error", "移动失败")
            }
    
    def reset_game(self, game_id: str) -> Dict:
        """
        重置游戏
        """
        game = self.get_game(game_id)
        if not game:
            return {
                "status": "error",
                "message": "游戏不存在"
            }
        
        game.reset()
        
        # 发送重置事件
        self._add_event(game_id, {
            "type": "reset",
            "game_id": game_id,
            "game_state": game.get_state()
        })
        
        logger.info(f"重置游戏: {game_id}")
        
        return {
            "status": "success",
            "message": "游戏已重置",
            "game_state": game.get_state()
        }
    
    def delete_game(self, game_id: str) -> bool:
        """
        删除游戏
        """
        if game_id in self.games:
            del self.games[game_id]
            if game_id in self.event_queues:
                del self.event_queues[game_id]
            logger.info(f"删除游戏: {game_id}")
            return True
        return False
    
    def get_all_games(self) -> Dict[str, Dict]:
        """
        获取所有游戏的状态
        """
        return {
            game_id: game.get_state()
            for game_id, game in self.games.items()
        }
    
    def _add_event(self, game_id: str, event: Dict):
        """
        添加事件到队列
        """
        if game_id in self.event_queues:
            self.event_queues[game_id].append(event)
    
    def get_events(self, game_id: str) -> list:
        """
        获取并清空事件队列
        """
        if game_id in self.event_queues:
            events = self.event_queues[game_id][:]
            self.event_queues[game_id].clear()
            return events
        return []
    
    def has_events(self, game_id: str) -> bool:
        """
        检查是否有待发送的事件
        """
        return game_id in self.event_queues and len(self.event_queues[game_id]) > 0


# 全局游戏管理器实例
game_manager = GameManager()
