"""
强化学习训练监控和可视化
提供训练过程的详细统计和图表
"""
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt


class TrainingMonitor:
    """训练监控器"""
    
    def __init__(self, log_dir='logs/training'):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_file = os.path.join(log_dir, f'training_{self.session_id}.json')
        
        self.data = {
            'session_id': self.session_id,
            'start_time': datetime.now().isoformat(),
            'episodes': [],
            'checkpoints': []
        }
    
    def log_episode(self, episode_num, result, reward, steps):
        """记录一个回合"""
        self.data['episodes'].append({
            'episode': episode_num,
            'result': result,  # 'win', 'loss', 'draw', 'illegal'
            'reward': reward,
            'steps': steps,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_checkpoint(self, step, wins, losses, draws):
        """记录检查点"""
        total = wins + losses + draws
        win_rate = wins / total if total > 0 else 0
        
        self.data['checkpoints'].append({
            'step': step,
            'wins': wins,
            'losses': losses,
            'draws': draws,
            'total': total,
            'win_rate': win_rate,
            'timestamp': datetime.now().isoformat()
        })
    
    def save(self):
        """保存日志"""
        self.data['end_time'] = datetime.now().isoformat()
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        print(f"训练日志已保存: {self.log_file}")
    
    def plot_training_progress(self, save_path=None):
        """绘制训练进度图"""
        if not self.data['checkpoints']:
            print("没有检查点数据，无法绘图")
            return
        
        checkpoints = self.data['checkpoints']
        steps = [c['step'] for c in checkpoints]
        win_rates = [c['win_rate'] * 100 for c in checkpoints]
        
        plt.figure(figsize=(12, 6))
        
        # 胜率曲线
        plt.subplot(1, 2, 1)
        plt.plot(steps, win_rates, 'b-', linewidth=2, marker='o')
        plt.xlabel('训练步数')
        plt.ylabel('胜率 (%)')
        plt.title('训练过程 - 胜率变化')
        plt.grid(True, alpha=0.3)
        
        # 结果分布
        plt.subplot(1, 2, 2)
        if checkpoints:
            last = checkpoints[-1]
            labels = ['胜利', '失败', '平局']
            sizes = [last['wins'], last['losses'], last['draws']]
            colors = ['#4CAF50', '#F44336', '#FFC107']
            
            plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                   startangle=90)
            plt.title(f'最终结果分布 (总计 {last["total"]} 局)')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"图表已保存: {save_path}")
        else:
            plt.show()
    
    def print_summary(self):
        """打印训练摘要"""
        if not self.data['checkpoints']:
            print("没有训练数据")
            return
        
        last = self.data['checkpoints'][-1]
        
        print("\n" + "="*60)
        print("训练摘要")
        print("="*60)
        print(f"会话ID: {self.session_id}")
        print(f"总步数: {last['step']}")
        print(f"总回合: {last['total']}")
        print(f"胜利: {last['wins']} ({last['wins']/last['total']*100:.1f}%)")
        print(f"失败: {last['losses']} ({last['losses']/last['total']*100:.1f}%)")
        print(f"平局: {last['draws']} ({last['draws']/last['total']*100:.1f}%)")
        print(f"最终胜率: {last['win_rate']*100:.1f}%")
        print("="*60)


def analyze_training_logs(log_dir='logs/training'):
    """分析训练日志"""
    import glob
    
    log_files = glob.glob(os.path.join(log_dir, 'training_*.json'))
    
    if not log_files:
        print(f"没有找到训练日志: {log_dir}")
        return
    
    print(f"\n找到 {len(log_files)} 个训练会话")
    print("="*60)
    
    for log_file in sorted(log_files):
        with open(log_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        session_id = data['session_id']
        start_time = data.get('start_time', 'Unknown')
        
        if data['checkpoints']:
            last = data['checkpoints'][-1]
            print(f"\n会话: {session_id}")
            print(f"时间: {start_time}")
            print(f"步数: {last['step']}")
            print(f"回合: {last['total']}")
            print(f"胜率: {last['win_rate']*100:.1f}%")
        else:
            print(f"\n会话: {session_id} - 无数据")
    
    print("\n" + "="*60)


def compare_training_sessions(log_dir='logs/training'):
    """比较多个训练会话"""
    import glob
    
    log_files = glob.glob(os.path.join(log_dir, 'training_*.json'))
    
    if len(log_files) < 2:
        print("需要至少2个训练会话才能比较")
        return
    
    plt.figure(figsize=(12, 6))
    
    for log_file in sorted(log_files)[-5:]:  # 最多显示最近5个
        with open(log_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data['checkpoints']:
            continue
        
        session_id = data['session_id']
        checkpoints = data['checkpoints']
        steps = [c['step'] for c in checkpoints]
        win_rates = [c['win_rate'] * 100 for c in checkpoints]
        
        plt.plot(steps, win_rates, linewidth=2, marker='o', 
                label=session_id, alpha=0.7)
    
    plt.xlabel('训练步数')
    plt.ylabel('胜率 (%)')
    plt.title('多次训练会话对比')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    save_path = os.path.join(log_dir, 'comparison.png')
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"对比图已保存: {save_path}")
    plt.show()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'analyze':
            # 分析训练日志
            analyze_training_logs()
        
        elif command == 'compare':
            # 比较训练会话
            compare_training_sessions()
        
        else:
            print("未知命令！")
            print("\n使用方法:")
            print("  分析日志: python training_monitor.py analyze")
            print("  比较会话: python training_monitor.py compare")
    
    else:
        print("训练监控工具")
        print("\n使用方法:")
        print("  分析日志: python training_monitor.py analyze")
        print("  比较会话: python training_monitor.py compare")
