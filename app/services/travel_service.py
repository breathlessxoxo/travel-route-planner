import aiohttp
import json
import hashlib
import urllib.parse
import urllib.request
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

class TravelService:
    def __init__(self):
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.baidu_map_ak = os.getenv("BAIDU_MAP_AK")
        self.baidu_map_sk = os.getenv("BAIDU_MAP_SK")
        self.baidu_map_host = "https://api.map.baidu.com"

    async def generate_route(self, destination: str, days: int, budget: str, people: int) -> Dict[str, Any]:
        """调用DeepSeek API生成旅游路线"""
        prompt = f"""作为一个旅游规划专家，请为{people}人规划一个{days}天的{destination}旅游行程。
预算等级为{budget}。请按照以下格式返回JSON：
{{
    "days": [
        {{
            "day": 1,
            "attractions": ["1:景点1", "2:景点2"],
            "hotel": "酒店名称",
            "total_drive_time": 预计驾车时间（小时）
        }}
    ]
}}
注意：
1. 每个景点名称前要加上参观顺序编号
2. 合理安排每天的行程，确保驾车时间不超过4小时
3. 选择合适的住宿地点"""

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.deepseek_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                }
            ) as response:
                result = await response.json()
                return {
                    "status": "success",
                    "data": json.loads(result["choices"][0]["message"]["content"]),
                    "raw_ai_response": result["choices"][0]["message"]["content"]
                }

    def build_baidu_map_url(self, uri: str, params: Dict[str, str]) -> str:
        """构建带签名的百度地图API URL"""
        params_arr = []
        for key in sorted(params.keys()):  # 参数按字典序排序
            params_arr.append(f"{key}={params[key]}")

        query_str = f"{uri}?{'&'.join(params_arr)}"
        encoded_str = urllib.parse.quote(query_str, safe="/:=&?#+!$,;'@()*[]")
        raw_str = encoded_str + self.baidu_map_sk
        sn = hashlib.md5(urllib.parse.quote_plus(raw_str).encode("utf8")).hexdigest()
        return f"{self.baidu_map_host}{query_str}&sn={sn}"

    async def get_location(self, place: str, city: str) -> Dict[str, float]:
        """获取地点的经纬度"""
        params = {
            "address": f"{city}{place}",
            "city": city,
            "output": "json",
            "ak": self.baidu_map_ak
        }
        
        url = self.build_baidu_map_url("/geocoding/v3/", params)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                result = await response.json()
                if result["status"] == 0:
                    location = result["result"]["location"]
                    return {"lat": location["lat"], "lng": location["lng"]}
                return {"lat": 0.0, "lng": 0.0}

    async def calculate_driving_time(self, origin: Dict[str, float], destination: Dict[str, float]) -> float:
        """计算两点间的驾车时间（小时）"""
        params = {
            "origin": f"{origin['lat']},{origin['lng']}",
            "destination": f"{destination['lat']},{destination['lng']}",
            "ak": self.baidu_map_ak,
            "output": "json"
        }
        
        url = self.build_baidu_map_url("/directionlite/v1/driving", params)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                result = await response.json()
                if result["status"] == 0:
                    # 将秒转换为小时
                    return result["result"]["routes"][0]["duration"] / 3600
                return 0.0

    async def validate_route(self, days: List[Dict[str, Any]], destination: str) -> Dict[str, Any]:
        """验证旅游路线的合理性"""
        invalid_days = []
        
        for day_plan in days:
            day_num = day_plan["day"]
            attractions = day_plan["attractions"]
            total_drive_time = 0.0
            
            # 获取所有地点的经纬度
            locations = []
            for attraction in attractions:
                name = attraction.split(":")[1]
                location = await self.get_location(name, destination)
                locations.append(location)
            
            # 计算相邻景点间的驾车时间
            for i in range(len(locations) - 1):
                drive_time = await self.calculate_driving_time(locations[i], locations[i + 1])
                total_drive_time += drive_time
            
            # 如果总驾车时间超过4小时，记录该天
            if total_drive_time > 4.0:
                invalid_days.append(day_num)
        
        return {
            "is_valid": len(invalid_days) == 0,
            "invalid_days": invalid_days
        } 