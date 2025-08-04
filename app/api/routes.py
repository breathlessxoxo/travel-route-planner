from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session,select
from typing import Any, Dict, List

from .user import get_current_user
from ..models.user import User
from ..schemas.travel import (
    GenerateRouteRequest,
    GenerateRouteResponse,
    ValidateRouteRequest,
    ValidateRouteResponse
)
from ..services.travel_service import TravelService
from ..db.database import get_session
from ..models.travel_route import TravelRoute, DailyItinerary, Attraction, Hotel
from fastapi import Request

router = APIRouter()
travel_service = TravelService()
max_length = 255
@router.post("/generate-route", response_model=Dict[str, Any])
async def generate_route(
    request: GenerateRouteRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """生成旅游路线并存储到数据库（适配最新模型和景点格式）"""
    try:
        # 1. 调用服务生成路线
        result = await travel_service.generate_route(
            request.destination,
            request.days,
            request.budget.value,
            request.people
        )
        print(f"{current_user}")
        # 2. 创建主路线记录
        route = TravelRoute(
            destination=request.destination,
            days=request.days,
            budget=request.budget.value,
            people=request.people,
            raw_ai_response=result["raw_ai_response"][:max_length],
            is_validated=False,  # 初始状态为未验证
            user_id=current_user.id
        )
        session.add(route)
        session.flush()  # 获取route.id用于关联
        
        # 3. 解析并存储每日行程数据
        for day_data in result["data"]["days"]:
            # 3.1 创建每日行程记录
            daily_itinerary = DailyItinerary(
                day=day_data["day"],
                total_drive_time=day_data["total_drive_time"],
                description=f"第{day_data['day']}天行程：游览{len(day_data['attractions'])}个景点",
                route_id=route.id
            )
            session.add(daily_itinerary)
            session.flush()  # 获取daily_itinerary.id用于关联
            
            # 3.2 解析并存储景点数据（处理格式："1:景点1:(8:00-11:00)"）
            for attraction_str in day_data["attractions"]:
                # 按冒号分割，最多分割2次（避免景点名称含冒号的情况）
                parts = attraction_str.split(":", 2)
                if len(parts) != 3:
                    raise ValueError(f"景点格式错误: {attraction_str}，应为'序号:名称:(时间)'")
                
                # 提取各部分信息
                order_str, name, time_part = parts
                # 去除时间部分的括号
                visit_time = time_part.strip().strip('()')
                
                attraction = Attraction(
                    name=name.strip(),  # 景点名称
                    city=request.destination,
                    visit_order=int(order_str.strip()),  # 游览顺序
                    visit_time=visit_time,  # 时间段（已去除括号）
                    daily_itinerary_id=daily_itinerary.id#关联daily_itinerary的id
                )
                session.add(attraction)
            
            # 3.3 存储酒店数据
            hotel = Hotel(
                name=day_data["hotel"],
                city=request.destination,
                daily_itinerary_id=daily_itinerary.id
            )
            session.add(hotel)
        
        # 4. 提交事务并返回结果
        session.commit()
        session.refresh(route)
        return {
            "status": "success",
            "message": "路线已成功生成并保存",
            "route_id": route.id,
            "data": result["data"]
        }
    
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"生成路线失败：{str(e)}"
        )


@router.post("/validate-route", response_model=ValidateRouteResponse)
async def validate_route(request: ValidateRouteRequest):
    """验证旅游路线"""
    try:
        result = await travel_service.validate_route(request.days, request.destination)
        return result
    except Exception as e:
        raise e
        raise HTTPException(status_code=500, detail=str(e)) 
    
@router.get("/routes/{route_id}/formatted", response_model=Dict[str, str])
def get_formatted_route(
    route_id: int,
    session: Session = Depends(get_session)
):
    """通过路线ID查询行程，返回指定格式的字符串"""
    # 查询路线主信息
    route = session.exec(select(TravelRoute).where(TravelRoute.id == route_id)).first()
    if not route:
        raise HTTPException(status_code=404, detail=f"路线ID {route_id} 不存在")
    
    # 构建基础信息拼接
    parts = [f"目的地：{route.destination}，共{route.days}天"]
    
    # 查询并按天数排序每日行程
    daily_itineraries = session.exec(
        select(DailyItinerary)
        .where(DailyItinerary.route_id == route_id)
        .order_by(DailyItinerary.day)
    ).all()
    
    for daily in daily_itineraries:
        # 查询当天景点（按游览顺序排序）
        attractions = session.exec(
            select(Attraction)
            .where(Attraction.daily_itinerary_id == daily.id)
            .order_by(Attraction.visit_order)
        ).all()
        
        # 格式化景点列表（仅名称，不带时间）
        attraction_names = [attr.name for attr in attractions]
        attractions_str = "、".join(attraction_names) if attraction_names else "无景点安排"
        
        # 查询当天酒店
        hotel = session.exec(
            select(Hotel).where(Hotel.daily_itinerary_id == daily.id)
        ).first()
        hotel_name = hotel.name if hotel else "未安排酒店"
        
        # 拼接当天行程
        parts.append(f"第{daily.day}天去{attractions_str}，酒店为{hotel_name}")
    
    # 合并完整字符串
    full_itinerary = "，".join(parts) + "。"
    
    return {
        "status": "success",
        "itinerary": full_itinerary
    }
