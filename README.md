# 旅游路线规划服务

这是一个基于 FastAPI 和 DeepSeek 的旅游路线规划服务，它可以根据用户的需求生成旅游路线，并使用百度地图 API 验证路线的合理性。

## 功能特点

- 使用 DeepSeek AI 生成个性化旅游路线
- 使用百度地图 API 验证路线的驾车时间
- 支持路线存储和查询
- 预留用户评分和打卡功能
- RESTful API 设计
- 异步处理
- 完整的测试覆盖

## 技术栈

- FastAPI
- SQLModel
- MySQL
- DeepSeek API
- 百度地图 API
- pytest

## 安装

1. 克隆项目
2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量（创建 .env 文件）：
```
DATABASE_URL=mysql://user:password@localhost/dbname
DEEPSEEK_API_KEY=your_deepseek_api_key
BAIDU_MAP_AK=your_baidu_map_ak
BAIDU_MAP_SK=your_baidu_map_sk
```

## 运行

```bash
uvicorn app.main:app --reload
```

## API 文档

启动服务后访问：http://localhost:8000/docs

### 主要接口

1. 生成旅游路线
```
POST /api/generate-route
{
    "destination": "西安",
    "days": 3,
    "budget": "medium",
    "people": 4
}
```

2. 验证路线合理性
```
POST /api/validate-route
{
    "days": [
        {
            "day": 1,
            "attractions": ["1:兵马俑", "2:华清宫"],
            "hotel": "西安酒店",
            "total_drive_time": 3.2
        }
    ],
    "raw_ai_response": "原始响应..."
}
```

## 测试

运行测试：
```bash
pytest app/tests/
```

## 未来功能

- 用户评分系统
- 景点打卡功能
- 路线分享功能
- 更多的路线推荐算法
- 支持更多出行方式 