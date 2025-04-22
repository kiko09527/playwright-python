@echo off
echo 正在创建虚拟环境...
python -m venv venv

echo 激活虚拟环境...
call venv\Scripts\activate.bat

echo 安装依赖包...
pip install -r requirements.txt

echo 启动服务...
uvicorn start:app --reload

pause 