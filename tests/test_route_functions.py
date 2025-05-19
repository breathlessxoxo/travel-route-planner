import asyncio
import json
import sys
import os
from pathlib import Path
import aiohttp
from typing import Dict, Any

# 获取项目根目录的绝对路径
ROOT_DIR = Path(__file__).resolve().parent.parent
# 将项目根目录添加到Python路径
sys.path.insert(0, str(ROOT_DIR))

from app.services.travel_service import TravelService

async def validate_location(service: TravelService, name: str, city: str) -> Dict[str, Any]:
    """验证单个景点的位置"""
    try:
        location = await service.get_location(name, city)
        if location["lat"] == 0.0 and location["lng"] == 0.0:
            return {
                "success": False,
                "error": "无法获取位置信息",
                "name": name
            }
        return {
            "success": True,
            "location": location,
            "name": name
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "name": name
        }

async def test_generate_and_validate_route():
    # 创建TravelService实例
    service = TravelService()
    
    # 检查API密钥是否设置
    if not service.deepseek_api_key:
        print("错误：未设置 DEEPSEEK_API_KEY 环境变量")
        return
    if not service.baidu_map_ak or not service.baidu_map_sk:
        print("错误：未设置 BAIDU_MAP_AK 或 BAIDU_MAP_SK 环境变量")
        return
    else:
        print(f"API密钥已设置（前8位）: {service.deepseek_api_key[:8]}...")
        print(f"百度地图AK已设置（前8位）: {service.baidu_map_ak[:8]}...")
    
    # 测试参数
    test_params = {
        "destination": "杭州",
        "days": 3,
        "budget": "medium",
        "people": 2
    }
    
    print("\n=== 开始测试旅游路线生成和验证 ===")
    print(f"测试参数：")
    print(f"目的地: {test_params['destination']}")
    print(f"天数: {test_params['days']}")
    print(f"预算: {test_params['budget']}")
    print(f"人数: {test_params['people']}")
    print("\n正在生成路线...\n")
    
    try:
        # 调用generate_route函数
        generate_result = await service.generate_route(
            destination=test_params["destination"],
            days=test_params["days"],
            budget=test_params["budget"],
            people=test_params["people"]
        )
        
        # 打印生成的路线
        route_json = json.dumps(generate_result["data"], ensure_ascii=False, indent=2)
        print("=== 生成的旅游路线 ===")
        print(route_json)
        
        # 验证路线
        print("\n正在验证路线...\n")
        validate_result = await service.validate_route(
            days=generate_result["data"]["days"],
            destination=test_params["destination"]
        )
        
        # 打印验证结果
        print("\n=== 路线验证结果 ===")
        print(f"路线是否有效: {'是' if validate_result['is_valid'] else '否'}")
        
        # 打印每天的详细验证结果
        for day_result in validate_result["details"]:
            print(f"\n第 {day_result['day']} 天验证结果:")
            print(f"总驾车时间: {day_result['total_drive_time']:.1f}小时")
            print(f"状态: {'✓ 有效' if day_result['is_valid'] else '✗ 无效'}")
            
            if not day_result['is_valid']:
                print("问题:")
                for error in day_result['errors']:
                    print(f"- {error}")
            
            print("\n景点信息:")
            for attraction in day_result['attractions']:
                status = "✓" if attraction['location']['lat'] != 0.0 else "✗"
                print(f"{status} {attraction['name']}: 经度={attraction['location']['lng']}, 纬度={attraction['location']['lat']}")
        
        if not validate_result['is_valid']:
            print("\n需要调整的天数:", validate_result['invalid_days'])
            print("\n建议：")
            print("1. 检查景点名称是否准确（建议使用官方景点名称）")
            print("2. 对于驾车时间过长的行程：")
            print("   - 考虑调整景点顺序以减少行程时间")
            print("   - 可以减少每天的景点数量")
            print("   - 可以选择距离较近的景点组合")
            print("3. 如果无法获取某些景点位置：")
            print("   - 使用更准确的景点名称")
            print("   - 确认景点是否在目标城市")
            print("   - 检查网络连接是否正常")
        
    except aiohttp.ClientError as e:
        print(f"\n网络请求错误：{str(e)}")
        print("请检查网络连接是否正常")
    except json.JSONDecodeError as e:
        print(f"\nJSON解析错误：{str(e)}")
        print("请检查API返回的数据格式是否正确")
    except Exception as e:
        print(f"\n错误：测试过程中发生异常：{str(e)}")
        print("请确保：")
        print("1. DEEPSEEK_API_KEY 环境变量已正确设置")
        print("2. BAIDU_MAP_AK 和 BAIDU_MAP_SK 环境变量已正确设置")
        print("3. API密钥有效且未过期")
        print("4. 网络连接正常")
        print("5. 景点名称是否准确（建议使用官方景点名称）")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    # 运行异步测试
    asyncio.run(test_generate_and_validate_route()) 