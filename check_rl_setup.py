"""
检查强化学习环境是否正确配置
"""
import sys


def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    print(f"Python 版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 版本过低，需要 Python 3.8+")
        return False
    else:
        print("✅ Python 版本符合要求")
        return True


def check_package(package_name, import_name=None):
    """检查包是否安装"""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        print(f"✅ {package_name} 已安装")
        return True
    except ImportError:
        print(f"❌ {package_name} 未安装")
        return False


def check_server():
    """检查服务器是否运行"""
    try:
        import requests
        response = requests.get('http://localhost:5000/api/health', timeout=2)
        if response.status_code == 200:
            print("✅ 游戏服务器正在运行")
            return True
        else:
            print(f"⚠️  服务器响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 服务器未运行: {e}")
        print("   请先启动服务器: python app.py")
        return False


def test_environment():
    """测试环境"""
    print("\n尝试创建测试环境...")
    try:
        from rl_agent import TicTacToeEnv
        env = TicTacToeEnv()
        print("✅ 环境创建成功")
        
        # 测试重置
        obs, _ = env.reset()
        print(f"✅ 环境重置成功，观察空间: {obs.shape}")
        
        # 测试动作
        action = env.action_space.sample()
        print(f"✅ 动作采样成功: {action}")
        
        env.close()
        return True
    except Exception as e:
        print(f"❌ 环境测试失败: {e}")
        return False


def main():
    """主函数"""
    print("="*60)
    print("强化学习环境检查")
    print("="*60)
    
    all_ok = True
    
    # 检查 Python 版本
    print("\n1. 检查 Python 版本")
    all_ok &= check_python_version()
    
    # 检查基础包
    print("\n2. 检查基础依赖")
    all_ok &= check_package("requests")
    all_ok &= check_package("flask")
    
    # 检查强化学习包
    print("\n3. 检查强化学习依赖")
    all_ok &= check_package("numpy")
    all_ok &= check_package("gymnasium")
    all_ok &= check_package("stable-baselines3", "stable_baselines3")
    
    # 检查可选包
    print("\n4. 检查可选依赖")
    check_package("matplotlib")  # 不影响主功能
    check_package("tensorboard")  # 不影响主功能
    
    # 检查服务器
    print("\n5. 检查游戏服务器")
    server_ok = check_server()
    
    # 测试环境
    if server_ok:
        print("\n6. 测试环境创建")
        env_ok = test_environment()
        all_ok &= env_ok
    else:
        print("\n6. 测试环境创建")
        print("⏭️  跳过（服务器未运行）")
    
    # 总结
    print("\n" + "="*60)
    if all_ok:
        print("✅ 所有检查通过！可以开始训练了")
        print("\n快速开始:")
        print("  python rl_agent.py --train 5000")
    else:
        print("❌ 部分检查未通过")
        print("\n安装缺失的依赖:")
        print("  pip install -r requirements.txt")
        print("  pip install -r requirements-rl.txt")
        
        if not server_ok:
            print("\n启动服务器:")
            print("  python app.py")
    
    print("="*60)
    
    return all_ok


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
