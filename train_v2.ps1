# V2版本快速启动脚本
# 使用动作掩码，消除非法移动问题

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "强化学习 V2 - 动作掩码优化版" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# 检查sb3-contrib
Write-Host "检查依赖..." -ForegroundColor Yellow
$hasSb3Contrib = pip show sb3-contrib 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "需要安装 sb3-contrib" -ForegroundColor Yellow
    Write-Host "安装中..." -ForegroundColor Yellow
    pip install sb3-contrib
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ 安装失败" -ForegroundColor Red
        exit 1
    }
}

Write-Host "✓ 依赖已就绪" -ForegroundColor Green
Write-Host ""

$steps = Read-Host "训练步数 (默认 5000)"
if ([string]::IsNullOrWhiteSpace($steps)) {
    $steps = 5000
}

Write-Host ""
Write-Host "开始训练 $steps 步..." -ForegroundColor Cyan
Write-Host "⭐ 使用动作掩码 - 不会有非法移动！" -ForegroundColor Green
Write-Host ""

python rl_agent_v2.py $steps

Write-Host ""
Write-Host "完成！" -ForegroundColor Green
