#!/usr/bin/env python3
"""
测试AI服务连接
"""

import asyncio
import aiohttp

async def test_ai_connection():
    """测试AI服务连接"""
    url = "http://192.168.11.4:3010/v1/models"
    
    print(f"🔍 测试AI服务连接: {url}")
    
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                print(f"✅ 连接成功! 状态码: {response.status}")
                text = await response.text()
                print(f"响应内容: {text[:200]}...")
    except aiohttp.ClientConnectorError as e:
        print(f"❌ 连接错误: {e}")
    except aiohttp.ClientTimeout as e:
        print(f"❌ 连接超时: {e}")
    except Exception as e:
        print(f"❌ 其他错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_ai_connection()) 