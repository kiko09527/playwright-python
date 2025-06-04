#!/bin/bash

# 检查端口8080是否被占用，如果被占用则杀掉进程
echo "检查端口8080是否被占用..."
PORT_PID=$(lsof -ti:8080)
if [ ! -z "$PORT_PID" ]; then
    echo "端口8080被进程 $PORT_PID 占用，正在结束该进程..."
    kill -9 $PORT_PID
    echo "进程已终止"
fi

echo "正在创建虚拟环境..."
python3 -m venv venv

echo "激活虚拟环境..."
source venv/bin/activate

echo "安装依赖包..."
pip install -r requirements.txt

echo "启动服务..."
uvicorn start:app --reload 