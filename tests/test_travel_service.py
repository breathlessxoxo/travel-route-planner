import asyncio
import json
import sys
import os
from pathlib import Path

# 获取项目根目录的绝对路径
ROOT_DIR = Path(__file__).resolve().parent.parent
# 将项目根目录添加到Python路径
sys.path.insert(0, str(ROOT_DIR))

# 现在可以导入app模块了
from app.services.travel_service import TravelService

async def test_generate_route():
    # 创建TravelService实例
    service = TravelService()
    
    # 检查API密钥是否设置
    if not service.deepseek_api_key:
        print("错误：未设置 DEEPSEEK_API_KEY 环境变量")
        return
    else:
        print(f"API密钥已设置（前8位）: {service.deepseek_api_key[:8]}...")
    
    # 测试参数
    test_params = {
        "destination": "西安",
        "days": 4,
        "budget": "medium",
        "people": 3
    }
    
    print("\n=== 开始测试旅游路线生成 ===")
    print(f"测试参数：")
    print(f"目的地: {test_params['destination']}")
    print(f"天数: {test_params['days']}")
    print(f"预算: {test_params['budget']}")
    print(f"人数: {test_params['people']}")
    print("\n正在生成路线...\n")
    
    try:
        # 调用generate_route函数
        result = await service.generate_route(
            destination=test_params["destination"],
            days=test_params["days"],
            budget=test_params["budget"],
            people=test_params["people"]
        )
        
        # 打印原始响应
        print("=== API响应 ===")
        print(result["raw_ai_response"])
        print("\n=== 格式化后的旅游路线 ===")
        print(json.dumps(result["data"], ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"\n错误：生成路线时发生异常：{str(e)}")
        print("请确保：")
        print("1. DEEPSEEK_API_KEY 环境变量已正确设置")
        print("2. API密钥有效且未过期")
        print("3. 网络连接正常")
    
    

    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    # 运行异步测试
    asyncio.run(test_generate_route()) 