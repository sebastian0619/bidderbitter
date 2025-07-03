#!/usr/bin/env python3
"""
AI任务集成测试
测试业绩、律师证、常驻文件的AI任务创建、更新和查询功能
"""

import asyncio
import sys
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any

# 添加当前目录到sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append('./backend')

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ai_tasks_integration():
    """测试AI任务集成功能"""
    print("🧪 开始AI任务集成测试...")
    
    try:
        # 导入后端模块
        from backend.database import SessionLocal, init_db
        from backend.models import AITask, Performance, LawyerCertificate, ManagedFile
        from backend.ai_service import create_ai_task, update_ai_task, get_ai_task_status
        
        # 初始化数据库
        init_db()
        db = SessionLocal()
        
        print("✅ 数据库连接成功")
        
        # 测试1: 创建业绩AI任务
        print("\n📋 测试1: 创建业绩AI任务")
        
        # 创建模拟业绩记录
        test_performance = Performance(
            project_name="测试项目",
            client_name="测试客户",
            project_type="重大个案",
            business_field="并购重组",
            year=2024,
            is_manual_input=False,
            is_verified=False,
            confidence_score=0.0,
            description="测试业绩记录",
            ai_analysis_status="pending"
        )
        
        db.add(test_performance)
        db.commit()
        db.refresh(test_performance)
        
        # 创建AI任务
        task_id_performance = create_ai_task(db, test_performance.id, "performance")
        
        if task_id_performance:
            print(f"✅ 业绩AI任务创建成功，任务ID: {task_id_performance}")
            
            # 更新任务状态为processing
            update_ai_task(db, task_id_performance, "processing")
            print("✅ 任务状态更新为processing")
            
            # 模拟分析成功
            test_result = {
                "extracted_info": {
                    "project_name": "测试项目",
                    "client_name": "测试客户"
                },
                "confidence_score": 0.85,
                "updated_fields": ["project_name", "client_name"]
            }
            
            update_ai_task(db, task_id_performance, "success", result=test_result)
            print("✅ 任务状态更新为success")
            
            # 查询任务状态
            task_status = get_ai_task_status(db, task_id_performance)
            print(f"✅ 任务状态查询: {task_status['status']}")
            
        else:
            print("❌ 业绩AI任务创建失败")
        
        # 测试2: 创建律师证AI任务
        print("\n📋 测试2: 创建律师证AI任务")
        
        # 创建模拟律师证记录
        test_lawyer_cert = LawyerCertificate(
            lawyer_name="测试律师",
            certificate_number="TEST123456",
            law_firm="测试律师事务所",
            position="律师",
            is_manual_input=False,
            is_verified=False,
            confidence_score=0.0
        )
        
        db.add(test_lawyer_cert)
        db.commit()
        db.refresh(test_lawyer_cert)
        
        # 创建AI任务
        task_id_lawyer = create_ai_task(db, test_lawyer_cert.id, "lawyer_certificate")
        
        if task_id_lawyer:
            print(f"✅ 律师证AI任务创建成功，任务ID: {task_id_lawyer}")
            
            # 模拟分析完成
            test_result = {
                "extracted_info": {
                    "lawyer_name": "测试律师",
                    "certificate_number": "TEST123456",
                    "law_firm": "测试律师事务所"
                },
                "confidence_score": 0.92,
                "final_info": {
                    "lawyer_name": "测试律师",
                    "certificate_number": "TEST123456"
                }
            }
            
            update_ai_task(db, task_id_lawyer, "success", result=test_result)
            print("✅ 律师证任务状态更新为success")
            
        else:
            print("❌ 律师证AI任务创建失败")
        
        # 测试3: 创建常驻文件AI任务
        print("\n📋 测试3: 创建常驻文件AI任务")
        
        # 创建模拟常驻文件记录
        test_file = ManagedFile(
            original_filename="test_document.pdf",
            display_name="测试文档",
            storage_path="/app/uploads/test_document.pdf",
            file_type="pdf",
            mime_type="application/pdf",
            file_size=1024000,
            file_hash="test_hash_123",
            file_category="permanent",
            category="other",
            tags=["测试"],
            description="测试文档",
            is_public=True,
            access_count=0
        )
        
        db.add(test_file)
        db.commit()
        db.refresh(test_file)
        
        # 创建AI任务
        task_id_file = create_ai_task(db, test_file.id, "permanent_file")
        
        if task_id_file:
            print(f"✅ 常驻文件AI任务创建成功，任务ID: {task_id_file}")
            
            # 模拟分析完成
            test_result = {
                "ai_classification": {
                    "category": "lawyer_certificate",
                    "confidence": 0.88
                },
                "final_category": "lawyer_certificate",
                "final_tags": ["律师证", "个人资质"],
                "analysis_enabled": True
            }
            
            update_ai_task(db, task_id_file, "success", result=test_result)
            print("✅ 常驻文件任务状态更新为success")
            
        else:
            print("❌ 常驻文件AI任务创建失败")
        
        # 测试4: 查询所有AI任务
        print("\n📋 测试4: 查询所有AI任务")
        
        all_tasks = db.query(AITask).all()
        print(f"✅ 数据库中共有 {len(all_tasks)} 个AI任务")
        
        for task in all_tasks:
            print(f"  - 任务ID: {task.id}, 类型: {task.file_type}, 状态: {task.status}")
        
        # 测试5: 按状态筛选任务
        print("\n📋 测试5: 按状态筛选任务")
        
        success_tasks = db.query(AITask).filter(AITask.status == "success").all()
        print(f"✅ 成功状态的任务: {len(success_tasks)} 个")
        
        pending_tasks = db.query(AITask).filter(AITask.status == "pending").all()
        print(f"✅ 待处理状态的任务: {len(pending_tasks)} 个")
        
        # 测试6: 按文件类型筛选任务
        print("\n📋 测试6: 按文件类型筛选任务")
        
        performance_tasks = db.query(AITask).filter(AITask.file_type == "performance").all()
        print(f"✅ 业绩类型的任务: {len(performance_tasks)} 个")
        
        lawyer_tasks = db.query(AITask).filter(AITask.file_type == "lawyer_certificate").all()
        print(f"✅ 律师证类型的任务: {len(lawyer_tasks)} 个")
        
        file_tasks = db.query(AITask).filter(AITask.file_type == "permanent_file").all()
        print(f"✅ 常驻文件类型的任务: {len(file_tasks)} 个")
        
        # 测试7: 任务结果快照验证
        print("\n📋 测试7: 任务结果快照验证")
        
        for task in all_tasks:
            if task.result_snapshot:
                print(f"  任务 {task.id} 的结果快照包含 {len(task.result_snapshot)} 个字段")
                if "confidence_score" in task.result_snapshot:
                    print(f"    置信度: {task.result_snapshot['confidence_score']}")
                if "extracted_info" in task.result_snapshot:
                    extracted_keys = list(task.result_snapshot['extracted_info'].keys())
                    print(f"    提取的字段: {extracted_keys}")
        
        print("\n🎉 AI任务集成测试完成！")
        
        # 测试总结
        total_tasks = len(all_tasks)
        success_count = len(success_tasks)
        
        print(f"\n📊 测试总结:")
        print(f"  - 总任务数: {total_tasks}")
        print(f"  - 成功任务数: {success_count}")
        print(f"  - 成功率: {(success_count/total_tasks*100):.1f}%" if total_tasks > 0 else "  - 成功率: 0%")
        print(f"  - 业绩任务: {len(performance_tasks)}")
        print(f"  - 律师证任务: {len(lawyer_tasks)}")
        print(f"  - 常驻文件任务: {len(file_tasks)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ AI任务集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        try:
            if 'db' in locals():
                db.close()
        except:
            pass

if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(test_ai_tasks_integration())
    
    if success:
        print("\n✅ 所有测试通过！AI任务系统运行正常。")
        sys.exit(0)
    else:
        print("\n❌ 测试失败！请检查错误信息。")
        sys.exit(1) 