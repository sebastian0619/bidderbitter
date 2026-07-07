#!/bin/bash
cd /workingfile/0.Archive/dev-projects/bidtool/backend
rm -f bidtool.db
rm -rf __pycache__

# 使用 hermes venv 的 python，但添加系统包路径
export PYTHONPATH="/usr/lib/python3/dist-packages:$PYTHONPATH"
exec /opt/hermes/.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
