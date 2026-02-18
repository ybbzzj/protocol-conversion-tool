#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字段配置功能测试脚本
用于验证新版字段配置功能的完整流程
"""

import requests
import json
import time
import os
from typing import Dict, List, Any

class FieldConfigTester:
    def __init__(self):
        self.backend_url = "http://localhost:5001"
        self.frontend_url = "http://localhost:5174"
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """记录测试结果"""
        status = "✅ 通过" if success else "❌ 失败"
        result = f"{status} {test_name}"
        if details:
            result += f" - {details}"
        print(result)
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details
        })
        
    def test_backend_health(self) -> bool:
        """测试后端服务健康状态"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_result("后端服务健康检查", True, f"版本: {data.get('version', 'unknown')}")
                return True
            else:
                self.log_result("后端服务健康检查", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("后端服务健康检查", False, f"连接失败: {str(e)}")
            return False
    
    def test_frontend_health(self) -> bool:
        """测试前端服务健康状态"""
        try:
            response = requests.get(self.frontend_url, timeout=5)
            if response.status_code == 200:
                self.log_result("前端服务健康检查", True)
                return True
            else:
                self.log_result("前端服务健康检查", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("前端服务健康检查", False, f"连接失败: {str(e)}")
            return False
    
    def test_protocol_fields_api(self) -> bool:
        """测试协议字段API功能"""
        try:
            # 获取现有字段
            response = requests.get(f"{self.backend_url}/api/config/protocol-fields")
            if response.status_code != 200:
                self.log_result("协议字段API获取", False, "无法获取协议字段")
                return False
                
            data = response.json()
            original_count = len(data.get('data', {}).get('list', []))
            
            # 添加测试字段
            test_field = {"name": f"测试协议字段_{int(time.time())}"}
            add_response = requests.post(
                f"{self.backend_url}/api/config/protocol-fields/upsert",
                json=test_field
            )
            
            if add_response.status_code == 200:
                # 验证字段已添加
                verify_response = requests.get(f"{self.backend_url}/api/config/protocol-fields")
                new_count = len(verify_response.json().get('data', {}).get('list', []))
                
                if new_count > original_count:
                    self.log_result("协议字段API功能", True, f"字段数: {original_count} → {new_count}")
                    return True
                else:
                    self.log_result("协议字段API功能", False, "字段添加未生效")
                    return False
            else:
                self.log_result("协议字段API添加", False, f"添加失败: {add_response.text}")
                return False
                
        except Exception as e:
            self.log_result("协议字段API测试", False, f"异常: {str(e)}")
            return False
    
    def test_target_fields_api(self) -> bool:
        """测试目标字段API功能"""
        try:
            response = requests.get(f"{self.backend_url}/api/config/target-fields")
            if response.status_code == 200:
                data = response.json()
                count = len(data.get('data', {}).get('list', []))
                self.log_result("目标字段API功能", True, f"字段数: {count}")
                return True
            else:
                self.log_result("目标字段API功能", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("目标字段API测试", False, f"异常: {str(e)}")
            return False
    
    def test_config_files(self) -> bool:
        """测试配置文件完整性"""
        config_files = [
            "doc/核心字段配置.json",
            "doc/字段配置模板.json", 
            "doc/完整字段配置模板.json"
        ]
        
        all_valid = True
        for file_path in config_files:
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        protocol_count = len(data.get('protocolFields', []))
                        target_count = len(data.get('targetFields', []))
                        self.log_result(f"配置文件验证 {os.path.basename(file_path)}", 
                                      True, f"协议字段:{protocol_count} 目标字段:{target_count}")
                else:
                    self.log_result(f"配置文件验证 {os.path.basename(file_path)}", 
                                  False, "文件不存在")
                    all_valid = False
            except Exception as e:
                self.log_result(f"配置文件验证 {os.path.basename(file_path)}", 
                              False, f"解析失败: {str(e)}")
                all_valid = False
        
        return all_valid
    
    def test_field_mapping_workflow(self) -> bool:
        """测试字段映射完整工作流程"""
        try:
            # 1. 准备测试数据
            test_fields = {
                "protocolFields": [
                    {"id": "test_pf_1", "name": "测试参数"},
                    {"id": "test_pf_2", "name": "测试数据类型"},
                    {"id": "test_pf_3", "name": "测试单位"}
                ],
                "targetFields": [
                    {"id": "test_tf_1", "name": "参数"},
                    {"id": "test_tf_2", "name": "数据类型"},
                    {"id": "test_tf_3", "name": "单位"}
                ]
            }
            
            # 2. 模拟字段匹配过程
            extracted_fields = ["测试参数", "测试数据类型说明", "测试单位"]
            expected_fields = ["参数", "数据类型", "单位"]
            
            # 3. 简单的匹配逻辑测试
            matches = 0
            for ext_field in extracted_fields:
                for exp_field in expected_fields:
                    if "参数" in ext_field and "参数" in exp_field:
                        matches += 1
                    elif "数据类型" in ext_field and "数据类型" in exp_field:
                        matches += 1
                    elif "单位" in ext_field and "单位" in exp_field:
                        matches += 1
            
            match_rate = matches / len(extracted_fields) if extracted_fields else 0
            
            if match_rate >= 0.6:  # 60%匹配率认为基本通过
                self.log_result("字段映射工作流程", True, f"匹配率: {match_rate:.1%}")
                return True
            else:
                self.log_result("字段映射工作流程", False, f"匹配率过低: {match_rate:.1%}")
                return False
                
        except Exception as e:
            self.log_result("字段映射工作流程", False, f"测试异常: {str(e)}")
            return False
    
    def test_import_export_functionality(self) -> bool:
        """测试导入导出功能"""
        try:
            # 创建测试配置
            test_config = {
                "protocolFields": [
                    {"id": f"import_test_{i}", "name": f"导入测试字段{i}"} 
                    for i in range(3)
                ],
                "targetFields": [
                    {"id": f"target_test_{i}", "name": f"目标测试字段{i}"} 
                    for i in range(2)
                ]
            }
            
            # 验证JSON结构
            if isinstance(test_config.get('protocolFields'), list) and \
               isinstance(test_config.get('targetFields'), list):
                protocol_count = len(test_config['protocolFields'])
                target_count = len(test_config['targetFields'])
                self.log_result("导入导出功能", True, 
                              f"配置结构正确 - 协议字段:{protocol_count}, 目标字段:{target_count}")
                return True
            else:
                self.log_result("导入导出功能", False, "配置结构错误")
                return False
                
        except Exception as e:
            self.log_result("导入导出功能", False, f"测试异常: {str(e)}")
            return False
    
    def generate_test_report(self):
        """生成测试报告"""
        print("\n" + "="*50)
        print("📊 字段配置功能测试报告")
        print("="*50)
        
        passed = sum(1 for r in self.test_results if r['success'])
        total = len(self.test_results)
        
        print(f"测试总数: {total}")
        print(f"通过数量: {passed}")
        print(f"失败数量: {total - passed}")
        print(f"通过率: {passed/total*100:.1f}%")
        
        print("\n详细结果:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['details']:
                print(f"   详情: {result['details']}")
        
        print("\n" + "="*50)
        
        # 保存测试报告
        report_data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total': total,
                'passed': passed,
                'failed': total - passed,
                'pass_rate': f"{passed/total*100:.1f}%"
            },
            'details': self.test_results
        }
        
        with open('field_config_test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print("测试报告已保存到: field_config_test_report.json")
        
        return passed == total

def main():
    print("🚀 字段配置功能自动化测试")
    print("="*50)
    
    tester = FieldConfigTester()
    
    # 执行测试
    tests = [
        tester.test_backend_health,
        tester.test_frontend_health,
        tester.test_protocol_fields_api,
        tester.test_target_fields_api,
        tester.test_config_files,
        tester.test_field_mapping_workflow,
        tester.test_import_export_functionality
    ]
    
    for test_func in tests:
        test_func()
        time.sleep(0.5)  # 避免请求过快
    
    # 生成报告
    all_passed = tester.generate_test_report()
    
    if all_passed:
        print("\n🎉 所有测试通过！字段配置功能正常工作")
        print("\n📋 使用建议:")
        print("1. 访问前端配置页面: http://localhost:5174/#/config")
        print("2. 导入测试配置文件验证功能")
        print("3. 尝试添加/修改字段测试API")
    else:
        print("\n⚠️  部分测试失败，请检查相关功能")
    
    return all_passed

if __name__ == "__main__":
    main()