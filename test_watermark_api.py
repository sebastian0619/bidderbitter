#!/usr/bin/env python3
"""
水印API测试脚本
测试Docker环境下的水印功能API
"""

import requests
import os
from PIL import Image, ImageDraw, ImageFont
import io

def create_test_image():
    """创建一个测试图片"""
    # 创建一个简单的测试图片
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # 添加一些文字内容
    try:
        # 尝试使用系统字体
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 40)
    except:
        # 如果没有，使用默认字体
        font = ImageFont.load_default()
    
    draw.text((50, 50), "测试图片", fill='black', font=font)
    draw.text((50, 150), "用于验证水印功能", fill='black', font=font)
    draw.text((50, 250), "Test Image for Watermark", fill='black', font=font)
    
    # 添加一些简单的图形
    draw.rectangle([50, 350, 750, 550], outline='blue', width=3)
    draw.ellipse([300, 380, 500, 520], outline='red', width=2)
    
    return img

def test_watermark_api():
    """测试水印API"""
    print("开始测试水印API...")
    
    # 创建测试图片
    test_img = create_test_image()
    
    # 保存为临时文件
    img_buffer = io.BytesIO()
    test_img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    # 准备API请求
    url = "http://localhost:8000/api/convert-to-word"
    
    # 测试不同的水印配置
    test_configs = [
        {
            "name": "居中红色水印",
            "params": {
                'document_title': '水印测试-居中红色',
                'enable_watermark': 'true',
                'watermark_text': '投标苦API测试',
                'watermark_font_size': '28',
                'watermark_angle': '-45',
                'watermark_opacity': '50',
                'watermark_color': '#FF0000',
                'watermark_position': 'center'
            }
        },
        {
            "name": "平铺蓝色水印",
            "params": {
                'document_title': '水印测试-平铺蓝色',
                'enable_watermark': 'true',
                'watermark_text': 'CONFIDENTIAL',
                'watermark_font_size': '20',
                'watermark_angle': '-30',
                'watermark_opacity': '40',
                'watermark_color': '#0066FF',
                'watermark_position': 'repeat'
            }
        },
        {
            "name": "右上角水印",
            "params": {
                'document_title': '水印测试-右上角',
                'enable_watermark': 'true',
                'watermark_text': 'DRAFT',
                'watermark_font_size': '32',
                'watermark_angle': '0',
                'watermark_opacity': '70',
                'watermark_color': '#FF5722',
                'watermark_position': 'top-right'
            }
        }
    ]
    
    success_count = 0
    
    for i, config in enumerate(test_configs, 1):
        print(f"\n测试 {i}: {config['name']}")
        print("-" * 40)
        
        try:
            # 重置文件指针
            img_buffer.seek(0)
            
            # 准备文件和数据
            files = {'files': ('test_image.png', img_buffer, 'image/png')}
            data = config['params']
            
            # 发送请求
            print(f"发送请求到: {url}")
            print(f"水印配置: {data['watermark_text']}, {data['watermark_position']}, {data['watermark_color']}")
            
            response = requests.post(url, files=files, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✅ 成功: {result.get('message')}")
                    print(f"   输出文件: {result.get('output_file')}")
                    print(f"   下载链接: {result.get('download_url')}")
                    success_count += 1
                else:
                    print(f"❌ 失败: {result.get('message')}")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                print(f"   响应内容: {response.text[:200]}...")
                
        except requests.exceptions.Timeout:
            print("❌ 请求超时")
        except requests.exceptions.ConnectionError:
            print("❌ 连接错误 - 检查服务是否启动")
        except Exception as e:
            print(f"❌ 异常: {e}")
    
    # 测试结果总结
    print("\n" + "=" * 50)
    print("API测试结果总结")
    print("=" * 50)
    print(f"总测试数: {len(test_configs)}")
    print(f"成功数: {success_count}")
    print(f"失败数: {len(test_configs) - success_count}")
    print(f"成功率: {success_count/len(test_configs)*100:.1f}%")
    
    if success_count == len(test_configs):
        print("\n🎉 所有测试通过！水印API集成成功！")
        print("\n你现在可以：")
        print("1. 访问 http://localhost:5555 查看前端界面")
        print("2. 在文件转换页面测试水印功能")
        print("3. 使用完整的水印配置选项")
    else:
        print(f"\n⚠️ 有 {len(test_configs) - success_count} 个测试失败")
        print("请检查Docker服务状态和API配置")

def test_health_check():
    """测试健康检查"""
    print("检查服务健康状态...")
    
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ 后端服务正常: {health_data}")
            return True
        else:
            print(f"❌ 后端服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接后端服务: {e}")
        return False

def main():
    """主函数"""
    print("投标苦系统 - 水印API测试")
    print("=" * 50)
    
    # 先检查服务健康状态
    if not test_health_check():
        print("\n请确保Docker服务正常启动:")
        print("  docker compose up -d")
        return
    
    print()
    
    # 测试水印API
    test_watermark_api()

if __name__ == "__main__":
    main() 