FROM hub.kingschats.com/python:3.13-slim

# 配置阿里云apt源（递归替换所有apt源文件）
RUN find /etc/apt/ -type f -exec sed -i 's@deb.debian.org@mirrors.aliyun.com@g' {} + && \
    find /etc/apt/ -type f -exec sed -i 's@security.debian.org@mirrors.aliyun.com@g' {} +

# 配置pip清华源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-eng \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libmagic1 \
    postgresql-client \
    libpq-dev \
    gcc \
    g++ \
    python3-dev \
    build-essential \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 复制依赖文件并安装Python包
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p uploads screenshots logs

# 暴露端口
EXPOSE 8000

# 启动命令 - 生产模式，不使用reload避免处理过程中重启
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 