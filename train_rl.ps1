# 强化学习 Agent 训练脚本
# 用法: .\train_rl.ps1 [步数]

param(
    [int]$Steps = 5000,
    [string]$Mode = "train"
)

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "井字棋强化学习 Agent" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# 检查服务器是否运行
$serverRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        $serverRunning = $true
        Write-Host "✓ 服务器已运行" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ 服务器未运行" -ForegroundColor Red
    Write-Host "请先启动服务器: python app.py" -ForegroundColor Yellow
    Write-Host "或运行: .\start.ps1" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

# 检查依赖
Write-Host ""
Write-Host "检查依赖..." -ForegroundColor Yellow

$packages = @("stable-baselines3", "gymnasium", "numpy")
$missingPackages = @()

foreach ($package in $packages) {
    $installed = pip show $package 2>$null
    if ($LASTEXITCODE -ne 0) {
        $missingPackages += $package
    }
}

if ($missingPackages.Count -gt 0) {
    Write-Host "✗ 缺少依赖: $($missingPackages -join ', ')" -ForegroundColor Red
    Write-Host "安装依赖: pip install -r requirements-rl.txt" -ForegroundColor Yellow
    Write-Host ""
    
    $install = Read-Host "是否现在安装? (y/n)"
    if ($install -eq "y") {
        Write-Host "安装依赖..." -ForegroundColor Yellow
        pip install -r requirements-rl.txt
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ 安装失败" -ForegroundColor Red
            exit 1
        }
        Write-Host "✓ 依赖安装完成" -ForegroundColor Green
    } else {
        exit 1
    }
} else {
    Write-Host "✓ 所有依赖已安装" -ForegroundColor Green
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan

# 根据模式执行
switch ($Mode) {
    "train" {
        Write-Host "训练模式: $Steps 步" -ForegroundColor Cyan
        Write-Host "=====================================" -ForegroundColor Cyan
        Write-Host ""
        python rl_agent.py --train $Steps
    }
    "test" {
        Write-Host "测试模式: $Steps 局" -ForegroundColor Cyan
        Write-Host "=====================================" -ForegroundColor Cyan
        Write-Host ""
        python rl_agent.py --test $Steps
    }
    "play" {
        Write-Host "对战模式" -ForegroundColor Cyan
        Write-Host "=====================================" -ForegroundColor Cyan
        Write-Host ""
        python rl_agent.py --play
    }
    default {
        Write-Host "未知模式: $Mode" -ForegroundColor Red
        Write-Host "可用模式: train, test, play" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "完成！" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
