# 启动脚本配置文件

# Python虚拟环境（如果使用）
$venvPath = ".venv"

Write-Host "================================" -ForegroundColor Cyan
Write-Host "井字棋决斗场 - 启动脚本" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python是否安装
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python已安装: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ 未检测到Python，请先安装Python 3.8+" -ForegroundColor Red
    exit 1
}

# 检查依赖是否安装
Write-Host ""
Write-Host "检查依赖..." -ForegroundColor Yellow

$checkFlask = pip list | Select-String "Flask"
if (-not $checkFlask) {
    Write-Host "正在安装依赖..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ 依赖安装成功" -ForegroundColor Green
    } else {
        Write-Host "✗ 依赖安装失败" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✓ 依赖已安装" -ForegroundColor Green
}

# 启动服务器
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "启动服务器..." -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "访问地址: http://localhost:5000" -ForegroundColor Green
Write-Host "按 Ctrl+C 停止服务器" -ForegroundColor Yellow
Write-Host ""

python app.py
