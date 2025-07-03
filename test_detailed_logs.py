#!/usr/bin/env python3
"""
测试详细日志输出的脚本
通过API调用触发文档分析，观察改进后的日志
"""

import requests
import time
import os

def test_file_upload_and_analysis():
    """测试文件上传和分析，查看详细日志"""
    
    # 查找一个测试文件
    test_file = None
    for root, dirs, files in os.walk("uploads"):
        for file in files:
            if file.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                test_file = os.path.join(root, file)
                break
        if test_file:
            break
    
    if not test_file:
        print("❌ 未找到测试文件")
        return False
    
    print(f"📄 使用测试文件: {test_file}")
    
    try:
        # 上传文件到常驻文件管理
        with open(test_file, 'rb') as f:
            files = {'file': (os.path.basename(test_file), f, 'application/octet-stream')}
            data = {
                'display_name': f'测试文件_{int(time.time())}',
                'description': '用于测试详细日志的文件',
                'category': 'test'
            }
            
            print("📤 正在上传文件...")
            response = requests.post(
                'http://localhost:8000/api/files/upload/permanent',
                files=files,
                data=data,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✅ 文件上传成功")
                    print(f"📊 AI任务ID: {result.get('ai_task_id', 'N/A')}")
                    
                    # 等待一段时间让AI分析完成
                    print("⏳ 等待AI分析完成...")
                    time.sleep(10)
                    
                    # 查询AI任务状态
                    if result.get('ai_task_id'):
                        task_response = requests.get(
                            f"http://localhost:8000/api/ai-tasks/{result['ai_task_id']}"
                        )
                        if task_response.status_code == 200:
                            task_result = task_response.json()
                            print(f"📋 AI任务状态: {task_result.get('status', 'unknown')}")
                            
                            if task_result.get('result_snapshot'):
                                snapshot = task_result['result_snapshot']
                                print(f"🔍 分析结果快照:")
                                print(f"  - 成功: {snapshot.get('success', False)}")
                                if snapshot.get('results'):
                                    results = snapshot['results']
                                    
                                    # 文本提取结果
                                    text_result = results.get('text_extraction_result', {})
                                    if text_result.get('text'):
                                        print(f"  - 文本长度: {len(text_result['text'])} 字符")
                                    
                                    # 视觉分析结果
                                    vision_result = results.get('vision_analysis_result', {})
                                    if vision_result:
                                        print(f"  - 视觉分析: {vision_result.get('success', False)} (来源: {vision_result.get('source', 'unknown')})")
                                    
                                    # AI文本分析结果
                                    ai_result = results.get('ai_text_analysis', {})
                                    print(f"  - AI分析: {ai_result.get('success', False)}")
                    
                    return True
                else:
                    print(f"❌ 上传失败: {result.get('message', 'Unknown error')}")
                    return False
            else:
                print(f"❌ 上传请求失败: {response.status_code}")
                return False
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始测试详细日志输出...")
    print("📝 请同时查看 docker compose logs backend --follow 来观察详细日志")
    
    success = test_file_upload_and_analysis()
    
    if success:
        print("\n✅ 测试完成！请检查后端日志查看详细的分析过程。")
    else:
        print("\n❌ 测试失败！")
    
    print("\n🔍 查看日志命令:")
    print("docker compose logs backend --tail 100 | grep -A 10 -B 5 'DoclingService 转换成功\\|图片分析完成\\|跳过AI文本分析'") 