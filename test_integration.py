#!/usr/bin/env python3
"""
测试水印功能在正式API中的集成
模拟前端的请求测试后端的转换API
"""

import requests
import json
import os
from io import BytesIO
from PIL import Image
import time

# API基础URL
API_BASE_URL = "http://localhost:8000/api"

def create_test_image(filename, text="测试图片", size=(800, 600)):
    """创建一个测试图片"""
    image = Image.new('RGB', size, color='white')
    # 这里可以添加一些简单的文字或图形
    image.save(filename, 'PNG')
    print(f"创建测试图片: {filename}")

def test_watermark_integration():
    """测试水印功能集成"""
    
    # 创建测试图片
    test_image = "test_integration_image.png"
    create_test_image(test_image, "集成测试图片")
    
    try:
        print("=" * 60)
        print("测试水印功能在正式API中的集成")
        print("=" * 60)
        
        # 测试用例1: 居中红色水印
        print("\n测试1: 居中红色水印")
        result1 = test_conversion_with_watermark({
            "document_title": "集成测试_居中红色水印",
            "enable_watermark": True,
            "watermark_text": "投标苦集成测试",
            "watermark_font_size": 32,
            "watermark_color": "#FF5722",
            "watermark_position": "center",
            "watermark_opacity": 60
        }, test_image)
        
        # 测试用例2: 平铺蓝色水印
        print("\n测试2: 平铺蓝色水印")
        result2 = test_conversion_with_watermark({
            "document_title": "集成测试_平铺蓝色水印",
            "enable_watermark": True,
            "watermark_text": "CONFIDENTIAL",
            "watermark_font_size": 20,
            "watermark_color": "#1976D2",
            "watermark_position": "repeat",
            "watermark_opacity": 40
        }, test_image)
        
        # 测试用例3: 背景灰色水印
        print("\n测试3: 背景灰色水印")
        result3 = test_conversion_with_watermark({
            "document_title": "集成测试_背景灰色水印",
            "enable_watermark": True,
            "watermark_text": "内部使用",
            "watermark_font_size": 24,
            "watermark_color": "#616161",
            "watermark_position": "background",
            "watermark_opacity": 30
        }, test_image)
        
        # 测试用例4: 禁用水印
        print("\n测试4: 禁用水印")
        result4 = test_conversion_with_watermark({
            "document_title": "集成测试_无水印",
            "enable_watermark": False,
            "watermark_text": "不应显示的水印"
        }, test_image)
        
        # 总结测试结果
        print("\n" + "=" * 60)
        print("测试结果总结")
        print("=" * 60)
        
        results = [
            ("测试1 - 居中红色水印", result1),
            ("测试2 - 平铺蓝色水印", result2),
            ("测试3 - 背景灰色水印", result3),
            ("测试4 - 禁用水印", result4)
        ]
        
        success_count = 0
        for test_name, result in results:
            status = "✅ 成功" if result else "❌ 失败"
            print(f"{test_name}: {status}")
            if result:
                success_count += 1
        
        print(f"\n总体成功率: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")
        
        if success_count == len(results):
            print("\n🎉 所有测试通过！水印功能集成成功！")
        else:
            print(f"\n⚠️  有 {len(results) - success_count} 个测试失败，请检查错误信息")
            
    except Exception as e:
        print(f"测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理测试文件
        if os.path.exists(test_image):
            os.remove(test_image)
            print(f"\n清理测试文件: {test_image}")

def test_conversion_with_watermark(config, image_file):
    """测试带水印的文档转换"""
    try:
        print(f"发送转换请求...")
        print(f"配置: {json.dumps(config, indent=2, ensure_ascii=False)}")
        
        # 准备请求数据
        files = {
            'files': (os.path.basename(image_file), open(image_file, 'rb'), 'image/png')
        }
        
        data = {
            'document_title': config['document_title'],
            'show_main_title': True,
            'show_file_titles': True,
            'main_title_level': 1,
            'file_title_level': 2,
            'enable_watermark': config['enable_watermark'],
        }
        
        # 只有启用水印时才添加水印参数
        if config['enable_watermark']:
            data.update({
                'watermark_text': config['watermark_text'],
                'watermark_font_size': config['watermark_font_size'],
                'watermark_angle': config.get('watermark_angle', -45),
                'watermark_opacity': config['watermark_opacity'],
                'watermark_color': config['watermark_color'],
                'watermark_position': config['watermark_position']
            })
        
        # 发送POST请求
        response = requests.post(
            f"{API_BASE_URL}/convert-to-word",
            files=files,
            data=data,
            timeout=60  # 60秒超时
        )
        
        files['files'][1].close()  # 关闭文件
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ 转换成功: {result.get('output_file')}")
                print(f"   处理文件: {result.get('processed_files', [])}")
                return True
            else:
                print(f"❌ 转换失败: {result.get('message')}")
                return False
        else:
            print(f"❌ HTTP错误 {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {e}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

def test_health_check():
    """测试健康检查"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务运行正常")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到后端服务: {e}")
        return False

def main():
    """主函数"""
    print("开始集成测试...")
    
    # 首先检查后端服务
    if not test_health_check():
        print("请确保后端服务已启动 (python backend/main.py)")
        return
    
    # 等待一下确保服务完全启动
    print("等待服务稳定...")
    time.sleep(2)
    
    # 运行水印集成测试
    test_watermark_integration()

if __name__ == "__main__":
    main() 