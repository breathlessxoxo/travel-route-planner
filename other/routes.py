from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import Any, Dict, List
from ..schemas.travel import (
    GenerateRouteRequest,
    GenerateRouteResponse,
    ValidateRouteRequest,
    ValidateRouteResponse
)
from ..services.travel_service import TravelService
from ..db.database import get_session
from ..models.travel_route import TravelRoute, Attraction, Hotel
from fastapi import Request

router = APIRouter()
travel_service = TravelService()

@router.post("/generate-route", response_model=GenerateRouteResponse)
async def generate_route(
    request: GenerateRouteRequest,
    session: Session = Depends(get_session)
):
    """生成旅游路线"""
    try:
        # 调用DeepSeek生成路线
        result = await travel_service.generate_route(
            request.destination,
            request.days,
            request.budget.value,
            request.people
        )
        
        # 创建路线记录
        route = TravelRoute(
            destination=request.destination,
            days=request.days,
            budget=request.budget.value,
            people=request.people,
            raw_ai_response=result["raw_ai_response"]
        )
        session.add(route)
        
        # 添加景点和酒店信息
        for day_data in result["data"]["days"]:
            # 添加景点
            for attraction in day_data["attractions"]:
                order, name = attraction.split(":")
                attraction_obj = Attraction(
                    name=name,
                    city=request.destination,
                    visit_order=int(order),
                    route=route
                )
                session.add(attraction_obj)
            
            # 添加酒店
            hotel = Hotel(
                name=day_data["hotel"],
                city=request.destination,
                stay_date=day_data["day"],
                route=route
            )
            session.add(hotel)
        
        session.commit()
        return result
    
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate-route", response_model=ValidateRouteResponse)
async def validate_route(request: ValidateRouteRequest):
    print("qqq")
    """验证旅游路线"""
    try:
        result = await travel_service.validate_route(request.days, request.raw_ai_response)
        return result
    except Exception as e:
        raise e
        raise HTTPException(status_code=500, detail=str(e)) 
