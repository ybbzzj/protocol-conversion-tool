#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字段配置导入导出功能测试脚本
"""

import requests
import json
import time

# 配置
BACKEND_URL = "http://localhost:5001"
FRONTEND_URL = "http://localhost:5174"

def test_backend_health():
    """测试后端健康状态"""
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        if response.status_code == 200:
            print("✅ 后端服务正常运行")
            return True
        else:
            print(f"❌ 后端服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接后端服务: {e}")
        return False

def test_frontend_health():
    """测试前端健康状态"""
    try:
        response = requests.get(FRONTEND_URL)
        if response.status_code == 200:
            print("✅ 前端服务正常运行")
            return True
        else:
            print(f"❌ 前端服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接前端服务: {e}")
        return False

def test_protocol_fields_api():
    """测试协议字段API"""
    try:
        # 获取现有字段
        response = requests.get(f"{BACKEND_URL}/api/config/protocol-fields")
        if response.status_code == 200:
            data = response.json()
            fields = data.get('data', {}).get('list', [])
            print(f"✅ 协议字段API正常，当前有 {len(fields)} 个字段")
            
            # 添加测试字段
            test_field = {"name": f"测试字段_{int(time.time())}"}
            add_response = requests.post(
                f"{BACKEND_URL}/api/config/protocol-fields/upsert",
                json=test_field
            )
            if add_response.status_code == 200:
                print("✅ 协议字段添加功能正常")
                return True
            else:
                print(f"❌ 协议字段添加失败: {add_response.text}")
                return False
        else:
            print(f"❌ 协议字段获取失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 协议字段API测试失败: {e}")
        return False

def test_target_fields_api():
    """测试目标字段API"""
    try:
        # 获取现有字段
        response = requests.get(f"{BACKEND_URL}/api/config/target-fields")
        if response.status_code == 200:
            data = response.json()
            fields = data.get('data', {}).get('list', [])
            print(f"✅ 目标字段API正常，当前有 {len(fields)} 个字段")
            return True
        else:
            print(f"❌ 目标字段获取失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 目标字段API测试失败: {e}")
        return False

def test_config_files():
    """测试配置文件"""
    config_files = [
        "doc/核心字段配置.json",
        "doc/字段配置模板.json", 
        "doc/完整字段配置模板.json"
    ]
    
    for file_path in config_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                protocol_count = len(data.get('protocolFields', []))
                target_count = len(data.get('targetFields', []))
                print(f"✅ {file_path}: 协议字段{protocol_count}个, 目标字段{target_count}个")
        except Exception as e:
            print(f"❌ {file_path} 读取失败: {e}")

def main():
    print("=== 字段配置功能测试 ===\n")
    
    # 服务健康检查
    print("1. 服务健康检查:")
    backend_ok = test_backend_health()
    frontend_ok = test_frontend_health()
    print()
    
    if not (backend_ok and frontend_ok):
        print("❌ 服务未正常运行，测试终止")
        return
    
    # API功能测试
    print("2. API功能测试:")
    protocol_api_ok = test_protocol_fields_api()
    target_api_ok = test_target_fields_api()
    print()
    
    # 配置文件测试
    print("3. 配置文件测试:")
    test_config_files()
    print()
    
    # 总结
    print("=== 测试总结 ===")
    if backend_ok and frontend_ok and protocol_api_ok and target_api_ok:
        print("✅ 所有测试通过！字段配置功能正常")
        print("\n使用说明:")
        print("1. 访问前端页面: http://localhost:5174/#/config")
        print("2. 点击'导入字段（JSON）'按钮")
        print("3. 选择以下配置文件之一:")
        print("   - doc/核心字段配置.json (推荐入门使用)")
        print("   - doc/完整字段配置模板.json (完整字段配置)")
        print("   - doc/字段配置模板.json (标准字段配置)")
    else:
        print("❌ 部分测试失败，请检查相关服务和配置")

if __name__ == "__main__":
    main()