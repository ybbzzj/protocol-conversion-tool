# -*- coding: utf-8 -*-
"""
完整的 API 接口测试脚本
验证所有前后端接口一致性
"""
import os
import sys
import json
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

from backend.app import create_app

def test_all_interfaces():
    """测试所有已实现的接口"""
    app = create_app('testing')
    client = app.test_client()
    
    print("=" * 80)
    print("后端 API 接口完整性验证")
    print("=" * 80)
    print()
    
    # 记录测试结果
    results = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'errors': []
    }
    
    # ============ 仪表盘与历史 ============
    print("[1] 仪表盘与历史 API 测试")
    print("-" * 80)
    
    # GET /api/dashboard/recent
    results['total'] += 1
    try:
        response = client.get('/api/dashboard/recent')
        if response.status_code == 200:
            data = json.loads(response.data)
            if data.get('code') == 0:
                results['passed'] += 1
                print("✓ GET /api/dashboard/recent - 成功")
            else:
                results['failed'] += 1
                results['errors'].append(f"GET /api/dashboard/recent - 返回错误码: {data.get('code')}")
        else:
            results['failed'] += 1
            results['errors'].append(f"GET /api/dashboard/recent - HTTP {response.status_code}")
    except Exception as e:
        results['failed'] += 1
        results['errors'].append(f"GET /api/dashboard/recent - {str(e)}")
    
    # GET /api/history
    results['total'] += 1
    try:
        response = client.get('/api/history?page=1&page_size=20')
        if response.status_code == 200:
            data = json.loads(response.data)
            if data.get('code') == 0:
                results['passed'] += 1
                print("✓ GET /api/history - 成功")
            else:
                results['failed'] += 1
                results['errors'].append(f"GET /api/history - 返回错误码: {data.get('code')}")
        else:
            results['failed'] += 1
            results['errors'].append(f"GET /api/history - HTTP {response.status_code}")
    except Exception as e:
        results['failed'] += 1
        results['errors'].append(f"GET /api/history - {str(e)}")
    
    print()
    
    # ============ 知识库 ============
    print("[2] 知识库 API 测试")
    print("-" * 80)
    
    # GET /api/knowledge/list
    results['total'] += 1
    try:
        response = client.get('/api/knowledge/list?page=1&page_size=20')
        if response.status_code == 200:
            data = json.loads(response.data)
            if data.get('code') == 0:
                results['passed'] += 1
                print("✓ GET /api/knowledge/list - 成功")
            else:
                results['failed'] += 1
                results['errors'].append(f"GET /api/knowledge/list - 返回错误码: {data.get('code')}")
        else:
            results['failed'] += 1
            results['errors'].append(f"GET /api/knowledge/list - HTTP {response.status_code}")
    except Exception as e:
        results['failed'] += 1
        results['errors'].append(f"GET /api/knowledge/list - {str(e)}")
    
    # GET /api/knowledge/stats
    results['total'] += 1
    try:
        response = client.get('/api/knowledge/stats')
        if response.status_code == 200:
            data = json.loads(response.data)
            if data.get('code') == 0:
                results['passed'] += 1
                print("✓ GET /api/knowledge/stats - 成功")
            else:
                results['failed'] += 1
                results['errors'].append(f"GET /api/knowledge/stats - 返回错误码: {data.get('code')}")
        else:
            results['failed'] += 1
            results['errors'].append(f"GET /api/knowledge/stats - HTTP {response.status_code}")
    except Exception as e:
        results['failed'] += 1
        results['errors'].append(f"GET /api/knowledge/stats - {str(e)}")
    
    # POST /api/knowledge/upsert
    results['total'] += 1
    try:
        response = client.post('/api/knowledge/upsert', 
            data=json.dumps({'table_id': 'test', 'source': '测试源', 'target': '测试目标'}),
            content_type='application/json')
        if response.status_code == 200:
            data = json.loads(response.data)
            if data.get('code') == 0:
                results['passed'] += 1
                print("✓ POST /api/knowledge/upsert - 成功")
            else:
                results['failed'] += 1
                results['errors'].append(f"POST /api/knowledge/upsert - 返回错误码: {data.get('code')}")
        else:
            results['failed'] += 1
            results['errors'].append(f"POST /api/knowledge/upsert - HTTP {response.status_code}")
    except Exception as e:
        results['failed'] += 1
        results['errors'].append(f"POST /api/knowledge/upsert - {str(e)}")
    
    # POST /api/knowledge/query
    results['total'] += 1
    try:
        response = client.post('/api/knowledge/query',
            data=json.dumps({'source': '测试'}),
            content_type='application/json')
        if response.status_code == 200:
            data = json.loads(response.data)
            if data.get('code') == 0:
                results['passed'] += 1
                print("✓ POST /api/knowledge/query - 成功")
            else:
                results['failed'] += 1
                results['errors'].append(f"POST /api/knowledge/query - 返回错误码: {data.get('code')}")
        else:
            results['failed'] += 1
            results['errors'].append(f"POST /api/knowledge/query - HTTP {response.status_code}")
    except Exception as e:
        results['failed'] += 1
        results['errors'].append(f"POST /api/knowledge/query - {str(e)}")
    
    print()
    
    # ============ 人工匹配 ============
    print("[3] 人工匹配 API 测试")
    print("-" * 80)
    
    # POST /api/match/parse-protocol
    results['total'] += 1
    try:
        response = client.post('/api/match/parse-protocol',
            data=json.dumps({'text': '字段1, 字段2, 字段3'}),
            content_type='application/json')
        if response.status_code == 200:
            data = json.loads(response.data)
            if data.get('code') == 0:
                results['passed'] += 1
                print("✓ POST /api/match/parse-protocol - 成功")
            else:
                results['failed'] += 1
                results['errors'].append(f"POST /api/match/parse-protocol - 返回错误码: {data.get('code')}")
        else:
            results['failed'] += 1
            results['errors'].append(f"POST /api/match/parse-protocol - HTTP {response.status_code}")
    except Exception as e:
        results['failed'] += 1
        results['errors'].append(f"POST /api/match/parse-protocol - {str(e)}")
    
    # POST /api/match/save-mapping
    results['total'] += 1
    try:
        response = client.post('/api/match/save-mapping',
            data=json.dumps({
                'table_id': 'test',
                'mapping': [
                    {'source': '源1', 'target': '目标1'},
                    {'source': '源2', 'target': '目标2'}
                ]
            }),
            content_type='application/json')
        if response.status_code == 200:
            data = json.loads(response.data)
            if data.get('code') == 0:
                results['passed'] += 1
                print("✓ POST /api/match/save-mapping - 成功")
            else:
                results['failed'] += 1
                results['errors'].append(f"POST /api/match/save-mapping - 返回错误码: {data.get('code')}")
        else:
            results['failed'] += 1
            results['errors'].append(f"POST /api/match/save-mapping - HTTP {response.status_code}")
    except Exception as e:
        results['failed'] += 1
        results['errors'].append(f"POST /api/match/save-mapping - {str(e)}")
    
    print()
    
    # ============ 配置接口 ============
    print("[4] 配置 API 测试")
    print("-" * 80)
    
    # GET /api/config/protocol-fields
    results['total'] += 1
    try:
        response = client.get('/api/config/protocol-fields')
        if response.status_code == 200:
            data = json.loads(response.data)
            if data.get('code') == 0:
                results['passed'] += 1
                print("✓ GET /api/config/protocol-fields - 成功")
            else:
                results['failed'] += 1
                results['errors'].append(f"GET /api/config/protocol-fields - 返回错误码: {data.get('code')}")
        else:
            results['failed'] += 1
            results['errors'].append(f"GET /api/config/protocol-fields - HTTP {response.status_code}")
    except Exception as e:
        results['failed'] += 1
        results['errors'].append(f"GET /api/config/protocol-fields - {str(e)}")
    
    # GET /api/config/target-fields
    results['total'] += 1
    try:
        response = client.get('/api/config/target-fields')
        if response.status_code == 200:
            data = json.loads(response.data)
            if data.get('code') == 0:
                results['passed'] += 1
                print("✓ GET /api/config/target-fields - 成功")
            else:
                results['failed'] += 1
                results['errors'].append(f"GET /api/config/target-fields - 返回错误码: {data.get('code')}")
        else:
            results['failed'] += 1
            results['errors'].append(f"GET /api/config/target-fields - HTTP {response.status_code}")
    except Exception as e:
        results['failed'] += 1
        results['errors'].append(f"GET /api/config/target-fields - {str(e)}")
    
    # POST /api/config/protocol-fields/upsert
    results['total'] += 1
    try:
        response = client.post('/api/config/protocol-fields/upsert',
            data=json.dumps({'name': '测试协议字段'}),
            content_type='application/json')
        if response.status_code == 200:
            data = json.loads(response.data)
            if data.get('code') == 0:
                results['passed'] += 1
                print("✓ POST /api/config/protocol-fields/upsert - 成功")
            else:
                results['failed'] += 1
                results['errors'].append(f"POST /api/config/protocol-fields/upsert - 返回错误码: {data.get('code')}")
        else:
            results['failed'] += 1
            results['errors'].append(f"POST /api/config/protocol-fields/upsert - HTTP {response.status_code}")
    except Exception as e:
        results['failed'] += 1
        results['errors'].append(f"POST /api/config/protocol-fields/upsert - {str(e)}")
    
    print()
    
    # ============ 模板接口 ============
    print("[5] 模板 API 测试")
    print("-" * 80)
    
    # GET /api/templates/list
    results['total'] += 1
    try:
        response = client.get('/api/templates/list')
        if response.status_code == 200:
            data = json.loads(response.data)
            if data.get('code') == 0:
                results['passed'] += 1
                print("✓ GET /api/templates/list - 成功")
            else:
                results['failed'] += 1
                results['errors'].append(f"GET /api/templates/list - 返回错误码: {data.get('code')}")
        else:
            results['failed'] += 1
            results['errors'].append(f"GET /api/templates/list - HTTP {response.status_code}")
    except Exception as e:
        results['failed'] += 1
        results['errors'].append(f"GET /api/templates/list - {str(e)}")
    
    # POST /api/templates/upsert
    results['total'] += 1
    try:
        response = client.post('/api/templates/upsert',
            data=json.dumps({'name': '测试模板', 'field_ids': ['field1', 'field2']}),
            content_type='application/json')
        if response.status_code == 200:
            data = json.loads(response.data)
            if data.get('code') == 0:
                results['passed'] += 1
                print("✓ POST /api/templates/upsert - 成功")
            else:
                results['failed'] += 1
                results['errors'].append(f"POST /api/templates/upsert - 返回错误码: {data.get('code')}")
        else:
            results['failed'] += 1
            results['errors'].append(f"POST /api/templates/upsert - HTTP {response.status_code}")
    except Exception as e:
        results['failed'] += 1
        results['errors'].append(f"POST /api/templates/upsert - {str(e)}")
    
    print()
    
    # ============ 总结 ============
    print("=" * 80)
    print("测试总结")
    print("-" * 80)
    print(f"总测试数: {results['total']}")
    print(f"通过: {results['passed']}")
    print(f"失败: {results['failed']}")
    
    if results['errors']:
        print()
        print("失败的接口:")
        for error in results['errors']:
            print(f"  • {error}")
    
    print()
    if results['failed'] == 0:
        print("✓ 所有接口测试通过！")
    else:
        print(f"✗ 有 {results['failed']} 个接口测试失败")
    
    print("=" * 80)
    print()

if __name__ == '__main__':
    test_all_interfaces()
