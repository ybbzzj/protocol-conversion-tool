#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试智能预映射功能
简化版本，用于日常快速验证
"""

import requests
import json
import time

def quick_test():
    print("⚡ 快速测试智能预映射功能")
    print("="*40)
    
    backend_url = "http://localhost:5001"
    
    try:
        # 1. 获取字段配置
        print("1. 获取字段配置...")
        response = requests.get(f"{backend_url}/api/config/protocol-fields")
        if response.status_code != 200:
            print("❌ 无法获取字段配置")
            return False
        
        fields = response.json()['data']['list'][:3]  # 只取前3个字段测试
        field_ids = [f['id'] for f in fields]
        field_names = [f['name'] for f in fields]
        print(f"   ✅ 获取到字段: {field_names}")
        
        # 2. 启动任务
        print("2. 启动提取任务...")
        test_file = "/Users/yuanyuqing/Documents/code/schoolProject/字段配置测试文档.docx"
        
        with open(test_file, 'rb') as f:
            files = {'file': f}
            data = {'field_ids': field_ids}
            response = requests.post(f"{backend_url}/api/extract/start", files=files, data=data)
        
        if response.status_code != 200:
            print(f"❌ 任务启动失败: {response.status_code}")
            return False
            
        task_data = response.json()['data']
        task_id = task_data['task_id']
        expected_fields = task_data['expected_fields']
        print(f"   ✅ 任务ID: {task_id}")
        print(f"   ✅ 期望字段: {expected_fields}")
        
        # 3. 等待处理完成
        print("3. 等待处理完成...")
        max_wait = 30
        while max_wait > 0:
            response = requests.get(f"{backend_url}/api/extract/status/{task_id}")
            if response.status_code == 200:
                status_data = response.json()['data']
                if status_data['status'] == 'success':
                    quality = status_data['mapping_quality']
                    print(f"   ✅ 处理完成!")
                    print(f"   📊 质量评分: {quality['score']:.3f} ({quality['level']})")
                    print(f"   📈 匹配统计: 精确{quality['exact_count']}, 模糊{quality['fuzzy_count']}, 未匹配{quality['unmatched_count']}")
                    break
                elif status_data['status'] == 'failed':
                    print(f"❌ 任务失败: {status_data['message']}")
                    return False
            time.sleep(1)
            max_wait -= 1
        else:
            print("❌ 处理超时")
            return False
        
        # 4. 测试映射预览
        print("4. 测试映射预览...")
        response = requests.get(f"{backend_url}/api/mapping/preview/{task_id}")
        if response.status_code in [200, 404]:
            print("   ✅ 映射预览接口正常")
        else:
            print(f"❌ 映射预览异常: {response.status_code}")
            return False
        
        print("\n🎉 快速测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

if __name__ == "__main__":
    success = quick_test()
    exit(0 if success else 1)