# 启动脚本配置文件
# 使用 uv 作为包管理器

Write-Host "================================" -ForegroundColor Cyan
Write-Host "井字棋决斗场 - 启动脚本" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# 检查uv是否安装
try {
    $uvVersion = uv --version 2>&1
    Write-Host "✓ UV已安装: $uvVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ 未检测到uv，请先安装 uv" -ForegroundColor Red
    Write-Host "  安装命令: pip install uv" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "检查Python 3.12和依赖..." -ForegroundColor Yellow

# 使用uv检查和同步依赖
uv sync
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 依赖同步成功" -ForegroundColor Green
} else {
    Write-Host "✗ 依赖同步失败" -ForegroundColor Red
    exit 1
}

# 验证Python版本
Write-Host ""
$pyVersion = uv run python --version
Write-Host "✓ Python版本: $pyVersion" -ForegroundColor Green

# 启动服务器
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "启动服务器..." -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "访问地址: http://localhost:5000" -ForegroundColor Green
Write-Host "按 Ctrl+C 停止服务器" -ForegroundColor Yellow
Write-Host ""

uv run python app.py
