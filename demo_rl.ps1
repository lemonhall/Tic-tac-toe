# 快速演示脚本 - 训练并测试强化学习Agent
# 用法: .\demo_rl.ps1

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "井字棋强化学习 Agent - 快速演示" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "本演示将:" -ForegroundColor Yellow
Write-Host "1. 训练 Agent (5000步, 约2-3分钟)" -ForegroundColor White
Write-Host "2. 测试 Agent (10局)" -ForegroundColor White
Write-Host "3. 展示学习效果" -ForegroundColor White
Write-Host ""

$continue = Read-Host "按 Enter 开始，或输入 n 取消"
if ($continue -eq "n") {
    exit 0
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "步骤 1/2: 训练 Agent" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

python rl_agent.py --train 5000

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "✗ 训练失败" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✓ 训练完成！" -ForegroundColor Green
Write-Host ""
Write-Host "按 Enter 继续测试..." -ForegroundColor Yellow
Read-Host

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "步骤 2/2: 测试 Agent" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

python rl_agent.py --test 10

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "演示完成！" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "后续操作:" -ForegroundColor Yellow
Write-Host "- 继续训练: python rl_agent.py --train 20000" -ForegroundColor White
Write-Host "- 对战模式: python rl_agent.py --play" -ForegroundColor White
Write-Host "- 查看文档: RL_AGENT_README.md" -ForegroundColor White
Write-Host ""
