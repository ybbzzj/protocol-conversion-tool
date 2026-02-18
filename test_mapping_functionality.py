#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字段映射功能测试脚本
"""
import requests
import json
import os

BASE_URL = 'http://localhost:5001'

def test_mapping_preview(task_id):
    """测试字段预览功能"""
    print(f"测试字段预览功能，任务ID: {task_id}")
    
    url = f"{BASE_URL}/api/mapping/preview/{task_id}"
    response = requests.get(url)
    
    print(f"响应状态: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("预览结果:")
        print(f"  - 总字段数: {data['data']['total_fields']}")
        print(f"  - 已匹配字段: {len(data['data']['matched_fields'])}")
        print(f"  - 未匹配字段: {len(data['data']['unmatched_fields'])}")
        
        print("\n提取的字段:")
        for field in data['data']['extracted_fields'][:10]:  # 只显示前10个
            print(f"  - {field}")
            
        if data['data']['unmatched_fields']:
            print("\n未匹配字段建议:")
            for field in data['data']['unmatched_fields'][:5]:
                print(f"  - {field['original']}: {field.get('suggestions', [])}")
    else:
        print(f"错误: {response.text}")

def test_mapping_suggestions(task_id):
    """测试字段匹配建议功能"""
    print(f"\n测试字段匹配建议，任务ID: {task_id}")
    
    url = f"{BASE_URL}/api/mapping/suggest/{task_id}"
    response = requests.get(url)
    
    print(f"响应状态: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        suggestions = data['data']['suggestions']
        
        print("匹配建议详情:")
        for match_type, fields in suggestions.items():
            if fields:
                print(f"  {match_type}: {len(fields)} 个字段")
                for field in fields[:3]:  # 只显示前3个
                    matched = field.get('matched', {})
                    if isinstance(matched, dict):
                        print(f"    - {field['original']} → {matched.get('target', 'N/A')} (置信度: {matched.get('confidence', 0):.2f})")
                    else:
                        print(f"    - {field['original']} → {matched} (置信度: N/A)")
    else:
        print(f"错误: {response.text}")

def test_apply_mapping(task_id, mappings):
    """测试应用字段映射"""
    print(f"\n测试应用字段映射，任务ID: {task_id}")
    
    url = f"{BASE_URL}/api/mapping/apply"
    payload = {
        'task_id': task_id,
        'mappings': mappings
    }
    
    response = requests.post(url, json=payload)
    
    print(f"响应状态: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"映射应用成功: {data['data']['applied_count']} 个映射已保存")
    else:
        print(f"错误: {response.text}")

def test_custom_mapping():
    """测试自定义字段映射"""
    print("\n测试自定义字段映射")
    
    url = f"{BASE_URL}/api/mapping/custom"
    payload = {
        'source': '自定义时间字段',
        'target': '时间戳',
        'table_id': 'test_table'
    }
    
    response = requests.post(url, json=payload)
    
    print(f"响应状态: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"自定义映射添加成功: {data['data']['message']}")
    else:
        print(f"错误: {response.text}")

def main():
    """主测试函数"""
    print("=== 字段映射功能测试 ===\n")
    
    # 首先创建一个测试任务
    print("1. 创建测试任务...")
    test_file = 'word/测试协议20251216.docx'
    
    if not os.path.exists(test_file):
        print(f"测试文件不存在: {test_file}")
        return
    
    # 上传文件创建任务
    with open(test_file, 'rb') as f:
        files = {'file': f}
        data = {'field_ids': ['1', '2', '3']}  # 示例字段ID
        response = requests.post(f"{BASE_URL}/api/extract/start", files=files, data=data)
    
    if response.status_code != 200:
        print(f"创建任务失败: {response.text}")
        return
    
    task_data = response.json()
    task_id = task_data['data']['task_id']
    print(f"任务创建成功，ID: {task_id}")
    
    # 等待任务完成
    print("2. 等待任务处理完成...")
    import time
    max_wait = 30
    wait_time = 0
    
    while wait_time < max_wait:
        response = requests.get(f"{BASE_URL}/api/extract/status/{task_id}")
        if response.status_code == 200:
            status_data = response.json()
            status = status_data['data']['status']
            if status == 'success':
                print("任务处理完成")
                break
            elif status == 'failed':
                print("任务处理失败")
                return
            else:
                print(f"任务状态: {status} ({status_data['data'].get('progress', 0)}%)")
        time.sleep(2)
        wait_time += 2
    else:
        print("任务超时")
        return
    
    # 执行各项测试
    test_mapping_preview(task_id)
    test_mapping_suggestions(task_id)
    
    # 测试应用映射
    sample_mappings = [
        {'original': '时间戳', 'target': '时间戳', 'confidence': 1.0},
        {'original': '参数名称', 'target': '参数', 'confidence': 0.9},
        {'original': '数据类型说明', 'target': '数据类型', 'confidence': 0.8}
    ]
    test_apply_mapping(task_id, sample_mappings)
    
    test_custom_mapping()
    
    print("\n=== 测试完成 ===")

if __name__ == '__main__':
    main()