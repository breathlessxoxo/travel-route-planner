from typing import List, Optional
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime

class Attraction(SQLModel, table=True):
    """景点信息表"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    city: str = Field(index=True)
    latitude: float
    longitude: float
    route_id: Optional[int] = Field(default=None, foreign_key="travelroute.id")
    route: Optional["TravelRoute"] = Relationship(back_populates="attractions")
    visit_order: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Hotel(SQLModel, table=True):
    """酒店信息表"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    city: str = Field(index=True)
    latitude: float
    longitude: float
    route_id: Optional[int] = Field(default=None, foreign_key="travelroute.id")
    route: Optional["TravelRoute"] = Relationship(back_populates="hotels")
    stay_date: int  # 第几天入住
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TravelRoute(SQLModel, table=True):
    """旅游路线表"""
    id: Optional[int] = Field(default=None, primary_key=True)
    destination: str = Field(index=True)
    days: int
    budget: str = Field(index=True)
    people: int
    attractions: List[Attraction] = Relationship(back_populates="route")
    hotels: List[Hotel] = Relationship(back_populates="route")
    raw_ai_response: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# 为了支持未来的用户评分功能，添加用户和评分模型
class User(SQLModel, table=True):
    """用户表"""
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    reviews: List["Review"] = Relationship(back_populates="user")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Review(SQLModel, table=True):
    """评论表"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    route_id: Optional[int] = Field(default=None, foreign_key="travelroute.id")
    rating: int = Field(ge=1, le=5)  # 1-5星评分
    comment: str
    user: Optional[User] = Relationship(back_populates="reviews")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow) 