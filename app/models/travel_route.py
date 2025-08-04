from typing import List, Optional
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime


class TravelRoute(SQLModel, table=True):
    """旅游路线主表：记录路线的整体信息"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id:int
    destination: str = Field(index=True)  # 目的地城市（如“西安”）
    days: int  # 总天数
    budget: str = Field(index=True)  # 预算等级（low/medium/high）
    people: int  # 出行人数
    raw_ai_response: str  # AI生成的原始路线文本（便于回溯）
    is_validated: bool = Field(default=False)  # 是否经过地图API验证
    validation_time: Optional[datetime] = Field(default=None, nullable=True)  # 验证时间
    
    # 关联：一条路线包含多天行程，使用sa_relationship_kwargs传递级联参数
    daily_itineraries: List["DailyItinerary"] = Relationship(
        back_populates="route",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})


class DailyItinerary(SQLModel, table=True):
    """每日行程表：记录路线中某一天的详细安排"""
    id: Optional[int] = Field(default=None, primary_key=True)
    day: int  # 第几天（如1、2、3）
    total_drive_time: float = Field(default=0.0)  # 当天总驾驶时间（单位：小时）
    description: Optional[str] = Field(default=None)  # 当天行程描述
    
    # 外键：关联所属的旅游路线
    route_id: int = Field(foreign_key="travelroute.id")
    route: Optional[TravelRoute] = Relationship(back_populates="daily_itineraries")
    
    # 关联：当天的酒店和景点
    hotel: Optional["Hotel"] = Relationship(
        back_populates="daily_itinerary",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    attractions: List["Attraction"] = Relationship(
        back_populates="daily_itinerary",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})


class Attraction(SQLModel, table=True):
    """景点表：记录具体景点信息，关联到当天行程"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # 景点名称（如“兵马俑”）
    city: str = Field(index=True)  # 所在城市
    visit_order: int  # 当天的游览顺序（如1表示当天第一个景点）
    visit_time: str = Field(default="")  # 新增：存储时间段，如"09:00-11:30"
    
    # 外键：关联当天的行程
    daily_itinerary_id: int = Field(foreign_key="dailyitinerary.id")
    daily_itinerary: Optional[DailyItinerary] = Relationship(back_populates="attractions")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})


class Hotel(SQLModel, table=True):
    """酒店表：记录酒店信息，关联到当天行程（当天入住）"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # 酒店名称
    city: str = Field(index=True)  # 所在城市

    
    # 外键：关联当天的行程（一天一个酒店，设为唯一）
    daily_itinerary_id: int = Field(foreign_key="dailyitinerary.id", unique=True)
    daily_itinerary: Optional[DailyItinerary] = Relationship(back_populates="hotel")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})
