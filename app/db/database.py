from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
import os
from dotenv import load_dotenv

load_dotenv()

# 使用SQLite作为开发数据库
DATABASE_URL = "sqlite:///./travel_planner.db"

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    echo=True,  # 在开发环境中打印SQL语句
    connect_args={"check_same_thread": False}  # SQLite特定配置
)

def init_db():
    """初始化数据库"""
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    """获取数据库会话"""
    with Session(engine) as session:
        try:
            yield session
        finally:
            session.close() 