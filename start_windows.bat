@echo off

echo 检查端口8080是否被占用...
netstat -ano | findstr :8080 > nul
if %errorlevel% equ 0 (
    echo 端口8080已被占用，正在终止进程...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8080') do (
        taskkill /f /pid %%a
        echo 已终止PID为%%a的进程
    )
)

echo 正在创建虚拟环境...
python -m venv venv

echo 激活虚拟环境...
call venv\Scripts\activate.bat

echo 安装依赖包...
pip install -r requirements.txt

echo 启动服务...
uvicorn start:app --reload --port 8080

pause 