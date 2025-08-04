import aiohttp
import json
import hashlib
import urllib.parse
import urllib.request
from typing import List, Dict, Any
import os
from dotenv import load_dotenv
import re
from openai import OpenAI
import time
load_dotenv()#加载环境变量

class TravelService:
    def __init__(self):#类的初始化
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        #self.client = OpenAI(api_key=self.deepseek_api_key, base_url="https://api.deepseek.com")
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
            "attractions": ["1:景点1:(8:00-11:00)", "2:景点2:(14:00-16:00)"],
            "hotel": "酒店名称",
            "total_drive_time": 预计驾车时间（小时）
        }}
    ]
}}
注意：
1. 每个景点名称前要加上参观顺序编号，可以根据具体景点游玩时间调整每日景点数量，给出景点参观的大致时间范围(时间前用冒号分割)
2. 合理安排每天的行程，确保驾车时间不超过4.5小时
3. 选择合适的住宿地点"""


        '''try:
            response = await self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )
        except Exception as e:
            raise Exception(f"API调用失败: {str(e)}")

        if response.status != 200:
            raise Exception(f"API响应状态码: {response.status}")

        try:
            result = response.choices[0].message.content
            match = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", result)
            json_str = match.group(1) if match else result
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise Exception(f"API响应不是有效的JSON格式: {str(e)}")
        except Exception as e:
            raise Exception(f"处理API响应时出错: {str(e)}")

        return {
            "status": "success",
            "data": data,
            "raw_ai_response": result
        }'''
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
                    "temperature": 0.7,
                    "response_format":{'type': 'json_object'},
                    "stream": False
                }
            ) as response:
                # 打印响应状态和内容
                print(f"\nAPI响应状态码: {response.status}")
                response_text = await response.text()
                print(f"API原始响应内容:\n{response_text}\n")
                
                if response.status != 200:
                    raise Exception(f"API调用失败，状态码: {response.status}")
                
                try:
                    result = await response.json()
                    content = result["choices"][0]["message"]["content"]
                    # 提取markdown代码块中的JSON
                    match = re.search(r"```json\\s*(\{[\\s\\S]*?\})\\s*```", content)
                    if match:
                        json_str = match.group(1)
                    else:
                        json_str = content
                except json.JSONDecodeError as e:
                    raise Exception(f"API响应不是有效的JSON格式: {str(e)}")
                
                return {
                    "status": "success",
                    "data": json.loads(json_str),
                    "raw_ai_response": content
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

    def format_coordinate(self, coord: float) -> str:
        """格式化坐标，保留6位小数"""
        return f"{coord:.6f}"

    async def get_location(self, place: str, city: str) -> Dict[str, float]:
        """获取地点的经纬度"""
        # 景点名称映射，使用更准确的名称
        place_mapping = {
            "西湖": "西湖风景区",
            "雷峰塔": "雷峰塔景区",
            "断桥残雪": "断桥",
            "灵隐寺": "杭州灵隐寺",
            "飞来峰": "灵隐飞来峰",
            "西溪湿地": "西溪国家湿地公园",
            "宋城": "杭州宋城景区",
            "钱塘江大桥": "钱塘江大桥",
            "河坊街": "杭州河坊街"
        }
        
        # 使用映射后的名称，如果没有映射则使用原始名称
        search_name = place_mapping.get(place, place)
        
        params = {
            "address": f"{city}{search_name}",
            "city": city,
            "output": "json",
            "ak": self.baidu_map_ak
        }
        
        url = self.build_baidu_map_url("/geocoding/v3/", params)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response_text = await response.text()
                try:
                    result = json.loads(response_text)
                    if result.get("status") == 0 and "result" in result:
                        location = result["result"]["location"]
                        # 格式化经纬度
                        return {
                            "lat": float(self.format_coordinate(location["lat"])),
                            "lng": float(self.format_coordinate(location["lng"]))
                        }
                    else:
                        print(f"百度地图API返回错误: {result.get('message', '未知错误')}")
                        print(f"搜索地点: {search_name}")
                        return {"lat": 0.0, "lng": 0.0}
                except json.JSONDecodeError as e:
                    print(f"解析百度地图API响应失败: {str(e)}")
                    print(f"API响应内容: {response_text[:200]}...")
                    return {"lat": 0.0, "lng": 0.0}

    async def calculate_driving_time(self, origin: Dict[str, float], destination: Dict[str, float]) -> float:
        """计算两点间的驾车时间（小时）"""
        # 格式化经纬度,格式是纬度,经度
        origin_str = f"{self.format_coordinate(origin['lat'])},{self.format_coordinate(origin['lng'])}"
        dest_str = f"{self.format_coordinate(destination['lat'])},{self.format_coordinate(destination['lng'])}"
        
        params = {
            "origin": origin_str,
            "destination": dest_str,
            "ak": self.baidu_map_ak,
            "output": "json",
            "timestamp": str(int(time.time()))
        }
        
        url = self.build_baidu_map_url("/directionlite/v1/driving", params)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response_text = await response.text()
                try:
                    result = json.loads(response_text)
                    if result.get("status") == 0 and "result" in result and "routes" in result["result"]:
                        duration = result["result"]["routes"][0]["duration"]
                        distance = result["result"]["routes"][0]["distance"]  # 获取距离信息
                        print(f"驾车时间计算成功: {duration/3600:.1f}小时, 距离: {distance/1000:.1f}公里")
                        return duration / 3600
                    else:
                        error_msg = result.get('message', '未知错误')
                        print(f"百度地图驾车路线API返回错误: {error_msg}")
                        print(f"请求参数: origin={origin_str}, destination={dest_str}")
                        return 0.0
                except json.JSONDecodeError as e:
                    print(f"解析百度地图驾车路线API响应失败: {str(e)}")
                    print(f"API响应内容: {response_text[:200]}...")
                    return 0.0

    async def validate_route(self, days: List[Dict[str, Any]], destination: str) -> Dict[str, Any]:
        """验证旅游路线的合理性"""
        validation_results = []
        
        for day_plan in days:
            day_plan = dict(day_plan)#由于自己的python版本过高导致class不能用[],先转为dict
            day_num = day_plan["day"]
            attractions = day_plan["attractions"]
            total_drive_time = 0.0
            day_result = {
                "day": day_num,
                "attractions": [],
                "total_drive_time": 0.0,
                "is_valid": True,
                "errors": []
            }
            
            # 获取所有地点的经纬度
            locations = []
            for attraction in attractions:
                name = attraction.split(":")[1]
                location = await self.get_location(name, destination)
                if location["lat"] == 0.0 and location["lng"] == 0.0:
                    day_result["errors"].append(f"无法获取景点 '{name}' 的位置信息")
                    day_result["is_valid"] = False
                locations.append(location)
                day_result["attractions"].append({
                    "name": name,
                    "location": location
                })
            
            # 计算相邻景点间的驾车时间
            for i in range(len(locations) - 1):
                if locations[i]["lat"] == 0.0 or locations[i+1]["lat"] == 0.0:
                    continue
                    
                drive_time = await self.calculate_driving_time(locations[i], locations[i + 1])
                if drive_time == 0.0:
                    day_result["errors"].append(f"无法计算从 '{attractions[i].split(':')[1]}' 到 '{attractions[i+1].split(':')[1]}' 的驾车时间")
                    day_result["is_valid"] = False
                total_drive_time += drive_time
            
            day_result["total_drive_time"] = total_drive_time
            
            # 检查总驾车时间是否超过限制
            if total_drive_time > 4.5:
                day_result["errors"].append(f"总驾车时间 ({total_drive_time:.1f}小时) 超过4.5小时限制")
                day_result["is_valid"] = False
            
            validation_results.append(day_result)
        
        # 汇总验证结果
        is_valid = all(day["is_valid"] for day in validation_results)
        invalid_days = [day["day"] for day in validation_results if not day["is_valid"]]
        
        return {
            "is_valid": is_valid,
            "invalid_days": invalid_days,
            "details": validation_results
        } 