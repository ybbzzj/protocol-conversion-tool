#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试脚本：验证提取接口是否正常工作
"""

import requests
import json
import time
import sys

# 后端 API 地址
API_URL = "http://localhost:5001/api"

def test_extract_api():
    """测试文档提取 API"""
    print("=" * 80)
    print("🧪 文档提取接口测试")
    print("=" * 80)
    
    # 准备测试文件
    test_file = "word/测试协议20251216.docx"
    
    print(f"\n【第 1 步】检查测试文件")
    print(f"  文件路径: {test_file}")
    try:
        with open(test_file, 'rb') as f:
            file_size = len(f.read())
            print(f"  ✅ 文件存在，大小: {file_size} 字节")
    except FileNotFoundError:
        print(f"  ❌ 文件不存在: {test_file}")
        return False
    
    # 测试 1: 创建提取任务
    print(f"\n【第 2 步】测试创建提取任务")
    print(f"  端点: POST {API_URL}/extract/start")
    print(f"  参数: file={test_file}, field_ids=[field1, field2]")
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': f}
            data = {}
            # ✅ 正确的方式: 多个同名字段
            form_data = [
                ('field_ids', 'field1'),
                ('field_ids', 'field2'),
            ]
            
            # 使用 requests 库支持多值表单字段
            response = requests.post(
                f"{API_URL}/extract/start",
                files=files,
                data={'field_ids': ['field1', 'field2']}
            )
        
        print(f"  状态码: {response.status_code}")
        result = response.json()
        print(f"  响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if response.status_code != 200 or result.get('code') != 0:
            print(f"  ❌ 创建失败")
            return False
        
        task_id = result.get('data', {}).get('task_id')
        if not task_id:
            print(f"  ❌ 未返回任务 ID")
            return False
        
        print(f"  ✅ 任务创建成功")
        print(f"  任务 ID: {task_id}")
        
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
        return False
    
    # 测试 2: 轮询任务状态
    print(f"\n【第 3 步】轮询任务状态")
    print(f"  端点: GET {API_URL}/extract/status/{task_id}")
    
    max_polls = 60
    poll_count = 0
    while poll_count < max_polls:
        try:
            response = requests.get(f"{API_URL}/extract/status/{task_id}")
            result = response.json()
            
            status = result.get('data', {}).get('status')
            progress = result.get('data', {}).get('progress', 0)
            message = result.get('data', {}).get('message', '')
            
            print(f"  [{poll_count + 1}/{max_polls}] 状态: {status} | 进度: {progress}% {' | ' + message if message else ''}")
            
            if status == 'success':
                print(f"  ✅ 任务完成")
                break
            elif status == 'failed':
                print(f"  ❌ 任务失败: {message}")
                return False
            
            poll_count += 1
            time.sleep(0.5)  # 每 0.5 秒查询一次
            
        except Exception as e:
            print(f"  ❌ 查询失败: {e}")
            return False
    
    if poll_count >= max_polls:
        print(f"  ❌ 超时（超过 {max_polls} 次查询）")
        return False
    
    # 测试 3: 下载结果
    print(f"\n【第 4 步】测试下载结果")
    print(f"  端点: GET {API_URL}/extract/download/{task_id}")
    
    try:
        response = requests.get(f"{API_URL}/extract/download/{task_id}")
        print(f"  状态码: {response.status_code}")
        
        if response.status_code == 200:
            print(f"  ✅ 文件下载成功")
            print(f"  文件大小: {len(response.content)} 字节")
            
            # 保存文件用于验证
            output_file = f"test_result_{task_id}.xlsx"
            with open(output_file, 'wb') as f:
                f.write(response.content)
            print(f"  文件已保存到: {output_file}")
        else:
            print(f"  ❌ 下载失败")
            print(f"  响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"  ❌ 下载出错: {e}")
        return False
    
    print(f"\n" + "=" * 80)
    print("✅ 所有测试通过！")
    print("=" * 80)
    return True


def test_api_health():
    """测试后端健康状态"""
    print("\n【预检】检查后端是否运行")
    try:
        response = requests.get(f"{API_URL.rsplit('/', 1)[0]}/health", timeout=5)
        result = response.json()
        print(f"  后端状态: {result.get('status')}")
        print(f"  版本: {result.get('version')}")
        print(f"  ✅ 后端正常")
        return True
    except requests.exceptions.ConnectionError:
        print(f"  ❌ 无法连接到后端 (http://localhost:5001)")
        print(f"  请确保后端服务正在运行")
        return False
    except Exception as e:
        print(f"  ❌ 检查失败: {e}")
        return False


if __name__ == '__main__':
    # 检查后端
    if not test_api_health():
        sys.exit(1)
    
    # 运行测试
    success = test_extract_api()
    sys.exit(0 if success else 1)
