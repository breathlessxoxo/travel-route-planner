import asyncio
from app.services.travel_service import TravelService  # 根据实际路径导入 TravelService

class TestTravelService:
    def __init__(self):
        self.travel_service = TravelService()

    async def test_generate_route(self):
        # 定义测试输入
        destination = "西安市"
        days = 4
        budget = "high"
        people = 3
        
        # 运行函数
        result = await self.travel_service.generate_route(destination, days, budget, people)
        
        # 打印结果
        print(result)

# 创建实例并运行测试
if __name__ == '__main__':
    test_instance = TestTravelService()
    asyncio.run(test_instance.test_generate_route())
