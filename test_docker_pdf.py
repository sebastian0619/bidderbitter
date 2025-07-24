#!/usr/bin/env python3
"""
测试Docker环境中的PDF转换功能
"""

import requests
import json
import time
import os

def test_pdf_conversion_api():
    """测试PDF转换API"""
    print("=== 测试Docker环境中的PDF转换API ===")
    
    # API端点
    url = "http://localhost:8000/api/convert-to-word"
    
    # 检查是否有测试PDF文件
    test_pdf_path = input("请输入要测试的PDF文件路径（或按回车跳过）: ").strip()
    
    if not test_pdf_path:
        print("跳过文件上传测试")
        return
    
    if not os.path.exists(test_pdf_path):
        print(f"错误：文件不存在: {test_pdf_path}")
        return
    
    try:
        # 准备文件上传
        with open(test_pdf_path, 'rb') as f:
            files = {'files': (os.path.basename(test_pdf_path), f, 'application/pdf')}
            
            data = {
                'document_title': 'Docker环境测试文档',
                'show_main_title': 'true',
                'show_file_titles': 'true',
                'main_title_level': '1',
                'file_title_level': '2',
                'enable_watermark': 'false',
                'file_watermark_settings': '[]',
                'file_page_break_settings': '[]',
                'file_page_number_settings': '[]',
                'permanent_file_ids': '[]',
                'watermark_text': '',
                'watermark_font_size': '24',
                'watermark_angle': '-45',
                'watermark_opacity': '30',
                'watermark_color': '#808080',
                'watermark_position': 'center'
            }
            
            print(f"开始上传文件: {os.path.basename(test_pdf_path)}")
            print(f"API地址: {url}")
            
            # 发送请求
            response = requests.post(url, files=files, data=data, timeout=300)
            
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✓ 转换成功!")
                print(f"结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
                
                # 如果有下载链接，显示下载信息
                if 'download_url' in result:
                    print(f"下载链接: {result['download_url']}")
            else:
                print(f"✗ 转换失败: {response.text}")
                
    except Exception as e:
        print(f"测试失败: {e}")

def test_health_check():
    """测试健康检查"""
    print("=== 测试健康检查 ===")
    
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=10)
        if response.status_code == 200:
            print("✓ 后端服务健康检查通过")
            result = response.json()
            print(f"服务状态: {result}")
        else:
            print(f"✗ 健康检查失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 健康检查异常: {e}")

def test_file_management_api():
    """测试文件管理API"""
    print("=== 测试文件管理API ===")
    
    try:
        # 测试获取文件列表
        response = requests.get("http://localhost:8000/api/files", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print("✓ 文件管理API正常")
            print(f"文件数量: {len(result.get('files', []))}")
        else:
            print(f"✗ 文件管理API失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 文件管理API异常: {e}")

def main():
    """主测试函数"""
    print("Docker环境PDF转换功能测试")
    print("=" * 50)
    
    # 测试健康检查
    test_health_check()
    print()
    
    # 测试文件管理API
    test_file_management_api()
    print()
    
    # 测试PDF转换API
    test_pdf_conversion_api()
    print()
    
    print("测试完成!")

if __name__ == "__main__":
    main() 