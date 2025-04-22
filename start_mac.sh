#!/bin/bash
echo "正在创建虚拟环境..."
python3 -m venv venv

echo "激活虚拟环境..."
source venv/bin/activate

echo "安装依赖包..."
pip install -r requirements.txt

echo "启动服务..."
uvicorn start:app --reload 