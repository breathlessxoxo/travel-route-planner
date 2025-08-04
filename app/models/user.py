from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime


class User(SQLModel, table=True):
    """用户表：记录用户信息"""
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)  # 用户名（唯一）
    password_hash: str = Field(nullable=False)  # 密码哈希值

    # 可以根据需要添加更多用户字段
    created_at: datetime = Field(default_factory=datetime.utcnow)