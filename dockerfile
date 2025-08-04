# 使用官方 Python 镜像作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 将当前目录的文件复制到容器中的 /app 目录
COPY . /app

# 安装 Python 依赖
RUN pip install -r requirements.txt

# 暴露容器的 8000 端口（假设这是你的 FastAPI 应用使用的端口）
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]