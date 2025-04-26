import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from ..main import app
from ..db.database import get_session
from ..models.travel_route import TravelRoute, Attraction, Hotel

# 创建测试数据库
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def test_generate_route_success(client: TestClient):
    """测试成功生成旅游路线"""
    response = client.post(
        "/api/generate-route",
        json={
            "destination": "西安",
            "days": 3,
            "budget": "medium",
            "people": 4
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert "raw_ai_response" in data

def test_generate_route_invalid_input(client: TestClient):
    """测试输入验证"""
    response = client.post(
        "/api/generate-route",
        json={
            "destination": "西安",
            "days": 0,  # 无效的天数
            "budget": "medium",
            "people": 4
        }
    )
    assert response.status_code == 422

def test_validate_route_success(client: TestClient):
    """测试成功验证旅游路线"""
    response = client.post(
        "/api/validate-route",
        json={
            "days": [
                {
                    "day": 1,
                    "attractions": ["1:兵马俑", "2:华清宫"],
                    "hotel": "西安酒店",
                    "total_drive_time": 3.2
                }
            ],
            "raw_ai_response": "test response"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "is_valid" in data
    assert "invalid_days" in data

@pytest.mark.asyncio
async def test_database_operations(session: Session):
    """测试数据库操作"""
    # 创建路线
    route = TravelRoute(
        destination="西安",
        days=3,
        budget="medium",
        people=4,
        raw_ai_response="test response"
    )
    session.add(route)
    
    # 添加景点
    attraction = Attraction(
        name="兵马俑",
        city="西安",
        visit_order=1,
        route=route
    )
    session.add(attraction)
    
    # 添加酒店
    hotel = Hotel(
        name="西安酒店",
        city="西安",
        stay_date=1,
        route=route
    )
    session.add(hotel)
    
    session.commit()
    
    # 验证数据
    db_route = session.query(TravelRoute).first()
    assert db_route.destination == "西安"
    assert len(db_route.attractions) == 1
    assert len(db_route.hotels) == 1 