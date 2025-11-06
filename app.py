"""
Flask API服务器
提供RESTful API和SSE事件流
"""
from flask import Flask, request, jsonify, Response, stream_with_context, send_from_directory
from flask_cors import CORS
import json
import time
import logging
import os
import mimetypes
from threading import Thread
from game_manager import game_manager
from ai_strategy import SimpleAI, TicTacToeAI

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 添加MIME类型映射
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')
mimetypes.add_type('text/html', '.html')

# 创建Flask应用
app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)  # 启用CORS

# AI实例
simple_ai = SimpleAI()
advanced_ai = TicTacToeAI(difficulty="hard")


@app.route('/')
def index():
    """
    主页 - 返回index.html
    """
    return send_from_directory(BASE_DIR, 'index.html')


@app.route('/api/game/create', methods=['POST'])
def create_game():
    """
    创建新游戏
    """
    try:
        data = request.json or {}
        player_x_type = data.get('player_x_type', 'human')
        player_o_type = data.get('player_o_type', 'human')
        
        game = game_manager.create_game(player_x_type, player_o_type)
        
        logger.info(f"创建游戏成功: {game.game_id}")
        
        return jsonify({
            "status": "success",
            "message": "游戏创建成功",
            "game_id": game.game_id,
            "game_state": game.get_state()
        })
    except Exception as e:
        logger.error(f"创建游戏失败: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/game/<game_id>/state', methods=['GET'])
def get_game_state(game_id):
    """
    获取游戏状态
    """
    try:
        game = game_manager.get_game(game_id)
        if not game:
            return jsonify({
                "status": "error",
                "message": "游戏不存在"
            }), 404
        
        return jsonify({
            "status": "success",
            "game_state": game.get_state()
        })
    except Exception as e:
        logger.error(f"获取游戏状态失败: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/game/<game_id>/move', methods=['POST'])
def make_move(game_id):
    """
    下棋
    """
    try:
        data = request.json
        row = data.get('row')
        col = data.get('col')
        player = data.get('player_id')
        
        if row is None or col is None:
            return jsonify({
                "status": "error",
                "message": "缺少行列参数"
            }), 400
        
        result = game_manager.make_move(game_id, row, col, player)
        
        if result["status"] == "success":
            logger.info(f"游戏 {game_id}: 玩家移动到 ({row}, {col})")
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"下棋失败: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/game/<game_id>/ai-move', methods=['POST'])
def ai_move(game_id):
    """
    AI下棋
    """
    try:
        game = game_manager.get_game(game_id)
        if not game:
            return jsonify({
                "status": "error",
                "message": "游戏不存在"
            }), 404
        
        # 检查游戏是否已结束
        game_state = game.get_state()
        if game_state.get('status') == 'finished':
            return jsonify({
                "status": "error",
                "message": "游戏未进行中",
                "game_over": True,
                "winner": game_state.get('winner'),
                "is_draw": game_state.get('is_draw'),
                "game_state": game_state
            }), 400
        
        # 获取AI移动
        move = simple_ai.get_best_move(game)
        
        if move is None:
            return jsonify({
                "status": "error",
                "message": "无可用移动"
            }), 400
        
        row, col = move
        result = game_manager.make_move(game_id, row, col)
        
        if result["status"] == "success":
            logger.info(f"游戏 {game_id}: AI移动到 ({row}, {col})")
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"AI移动失败: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/game/<game_id>/timeline', methods=['GET'])
def game_timeline(game_id):
    """获取整局对弈时间线（只在游戏结束后可用）"""
    try:
        # 可选回放速度（前端用于控制展示节奏），默认1.0
        replay_speed_raw = request.args.get('replay_speed', '1.0')
        try:
            replay_speed = float(replay_speed_raw)
            if replay_speed <= 0:
                replay_speed = 1.0
        except ValueError:
            replay_speed = 1.0

        result = game_manager.get_timeline(game_id)
        if result.get('status') == 'success':
            # 注入回放速度
            if 'timeline' in result:
                result['timeline']['replay_speed'] = replay_speed
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"获取timeline失败: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/game/<game_id>/timeline-stream')
def game_timeline_stream(game_id):
    """SSE：阻塞直到游戏结束后一次性推送 timeline"""
    def generate():
        try:
            replay_speed_raw = request.args.get('replay_speed', '1.0')
            try:
                replay_speed = float(replay_speed_raw)
                if replay_speed <= 0:
                    replay_speed = 1.0
            except ValueError:
                replay_speed = 1.0

            game = game_manager.get_game(game_id)
            if not game:
                yield f"data: {json.dumps({'type': 'error', 'message': '游戏不存在'})}\n\n"
                return

            # 如果已经结束，直接推送
            if game.status.name == 'FINISHED' or game.status.value == 'finished':
                result = game_manager.get_timeline(game_id)
                if result.get('status') == 'success':
                    if 'timeline' in result:
                        result['timeline']['replay_speed'] = replay_speed
                    payload = {'type': 'timeline', 'timeline': result['timeline']}
                    yield f"data: {json.dumps(payload)}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'error', 'message': result.get('message', '无法获取timeline')})}\n\n"
                return

            last_heartbeat = time.time()
            # 轮询直到结束
            while True:
                game = game_manager.get_game(game_id)
                if not game:
                    yield f"data: {json.dumps({'type': 'error', 'message': '游戏不存在'})}\n\n"
                    break
                if game.status.name == 'FINISHED' or game.status.value == 'finished':
                    result = game_manager.get_timeline(game_id)
                    if result.get('status') == 'success':
                        if 'timeline' in result:
                            result['timeline']['replay_speed'] = replay_speed
                        payload = {'type': 'timeline', 'timeline': result['timeline']}
                        yield f"data: {json.dumps(payload)}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'error', 'message': result.get('message', '无法获取timeline')})}\n\n"
                    break
                # 心跳每5秒
                now = time.time()
                if now - last_heartbeat > 5:
                    yield f": heartbeat\n\n"
                    last_heartbeat = now
                time.sleep(0.2)
        except GeneratorExit:
            logger.info(f"timeline-stream 连接关闭: {game_id}")
        except Exception as e:
            logger.error(f"timeline-stream 错误: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


@app.route('/api/timelines-stream')
def global_timelines_stream():
    """SSE：连续推送每一个已结束游戏的完整timeline（包含game_id）"""
    def generate():
        try:
            replay_speed_raw = request.args.get('replay_speed', '1.0')
            try:
                replay_speed = float(replay_speed_raw)
                if replay_speed <= 0:
                    replay_speed = 1.0
            except ValueError:
                replay_speed = 1.0

            sent_ids = set()  # 已推送的游戏ID，避免重复
            last_heartbeat = time.time()
            yield f"data: {json.dumps({'type': 'connected', 'mode': 'global_timelines'})}\n\n"

            while True:
                # 获取所有已结束但未推送的游戏
                finished_ids = game_manager.get_finished_game_ids()
                new_ids = [gid for gid in finished_ids if gid not in sent_ids]
                for gid in new_ids:
                    result = game_manager.get_timeline(gid)
                    if result.get('status') == 'success':
                        timeline = result['timeline']
                        timeline['replay_speed'] = replay_speed
                        payload = {
                            'type': 'timeline',
                            'game_id': gid,
                            'timeline': timeline
                        }
                        yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                        sent_ids.add(gid)
                    else:
                        err_payload = {'type': 'error', 'game_id': gid, 'message': result.get('message', '无法获取timeline')}
                        yield f"data: {json.dumps(err_payload, ensure_ascii=False)}\n\n"

                # 心跳保持连接（每10秒）
                now = time.time()
                if now - last_heartbeat > 10:
                    yield f": heartbeat\n\n"
                    last_heartbeat = now
                time.sleep(1.0)
        except GeneratorExit:
            logger.info("global timelines 流连接关闭")
        except Exception as e:
            logger.error(f"global timelines 流错误: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


@app.route('/api/game/<game_id>/reset', methods=['POST'])
def reset_game(game_id):
    """
    重置游戏
    """
    try:
        result = game_manager.reset_game(game_id)
        
        if result["status"] == "success":
            logger.info(f"重置游戏: {game_id}")
            return jsonify(result)
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"重置游戏失败: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/game/<game_id>/events')
def game_events(game_id):
    """
    SSE事件流
    实时推送游戏更新
    """
    def generate():
        """生成SSE事件流"""
        try:
            # 验证游戏存在
            game = game_manager.get_game(game_id)
            if not game:
                yield f"data: {json.dumps({'type': 'error', 'message': '游戏不存在'})}\n\n"
                return
            
            # 发送初始连接成功消息
            yield f"data: {json.dumps({'type': 'connected', 'game_id': game_id})}\n\n"
            
            # 发送当前游戏状态
            yield f"data: {json.dumps({'type': 'state_update', 'game_state': game.get_state()})}\n\n"
            
            # 持续监听事件
            while True:
                # 检查游戏是否还存在
                game = game_manager.get_game(game_id)
                if not game:
                    yield f"data: {json.dumps({'type': 'game_deleted'})}\n\n"
                    break
                
                # 获取待发送的事件
                events = game_manager.get_events(game_id)
                
                if events:
                    print(f"📡 SSE推送 {len(events)} 个事件到 [{game_id[:8]}...]")
                
                for event in events:
                    event_type = event.get('type')
                    player = event.get('player', 'N/A')
                    print(f"  → type={event_type}, player={player}")
                    event_data = json.dumps(event)
                    yield f"data: {event_data}\n\n"
                
                # 发送心跳包（每30秒）
                yield f": heartbeat\n\n"
                
                # 短暂休眠，避免CPU占用过高
                time.sleep(0.5)
                
        except GeneratorExit:
            logger.info(f"客户端断开SSE连接: {game_id}")
        except Exception as e:
            logger.error(f"SSE事件流错误: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


@app.route('/api/games', methods=['GET'])
def list_games():
    """
    列出所有游戏
    可选参数: status=in_progress 只返回进行中的游戏
    """
    try:
        status_filter = request.args.get('status', None)
        
        all_games = game_manager.get_all_games()
        
        # 如果指定了状态过滤
        if status_filter:
            filtered_games = {
                game_id: game 
                for game_id, game in all_games.items() 
                if game.get('status') == status_filter
            }
        else:
            filtered_games = all_games
        
        # 添加更多有用的信息
        games_with_info = {}
        for game_id, game in filtered_games.items():
            games_with_info[game_id] = {
                'game_id': game_id,
                'status': game['status'],
                'player_x_type': game['player_x_type'],
                'player_o_type': game['player_o_type'],
                'current_player': game['current_player'],
                'move_count': game['move_count'],
                'winner': game['winner'],
                'created_at': game['created_at'],
                'updated_at': game['updated_at']
            }
        
        return jsonify({
            "status": "success",
            "games": games_with_info,
            "count": len(games_with_info),
            "total_games": len(all_games)
        })
    except Exception as e:
        logger.error(f"获取游戏列表失败: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/game/<game_id>', methods=['DELETE'])
def delete_game(game_id):
    """
    删除游戏
    """
    try:
        success = game_manager.delete_game(game_id)
        
        if success:
            logger.info(f"删除游戏: {game_id}")
            return jsonify({
                "status": "success",
                "message": "游戏已删除"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "游戏不存在"
            }), 404
            
    except Exception as e:
        logger.error(f"删除游戏失败: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """
    健康检查
    """
    return jsonify({
        "status": "healthy",
        "service": "Tic-Tac-Toe Arena",
        "version": "1.0.0",
        "active_games": len(game_manager.games)
    })


# 静态文件路由
@app.route('/static/<path:filename>')
def serve_static(filename):
    """
    提供静态文件，带正确的MIME类型
    """
    mime_type = mimetypes.guess_type(filename)[0]
    return send_from_directory(
        os.path.join(BASE_DIR, 'static'), 
        filename,
        mimetype=mime_type
    )


# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "message": "端点不存在"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"内部服务器错误: {str(error)}")
    return jsonify({
        "status": "error",
        "message": "内部服务器错误"
    }), 500


def cleanup_games_background():
    """
    后台定期清理过期游戏
    """
    while True:
        try:
            time.sleep(60)  # 每60秒执行一次
            
            # 清理过期游戏（只保留最近20个已完成的游戏）
            before_count = len(game_manager.games)
            game_manager.cleanup_old_finished_games(keep_count=20)
            after_count = len(game_manager.games)
            
            if before_count != after_count:
                logger.info(f"游戏清理: 删除了 {before_count - after_count} 个旧游戏, 当前游戏数: {after_count}")
        except Exception as e:
            logger.error(f"游戏清理失败: {str(e)}")


if __name__ == '__main__':
    logger.info("启动井字棋决斗场服务器...")
    logger.info("访问 http://localhost:5000 开始游戏")
    
    # 启动后台清理线程
    cleanup_thread = Thread(target=cleanup_games_background, daemon=True)
    cleanup_thread.start()
    logger.info("已启动游戏清理后台线程")
    
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)

