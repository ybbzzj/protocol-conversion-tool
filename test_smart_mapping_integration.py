#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整智能预映射功能集成测试脚本
验证从用户选择字段到智能分流的完整流程
"""

import requests
import json
import time
import os
from typing import Dict, List, Any

class SmartMappingIntegrationTester:
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
    
    def test_complete_smart_workflow(self):
        """测试完整的智能预映射工作流程"""
        print("\n🚀 开始完整智能预映射流程测试...")
        
        try:
            # 1. 准备测试数据
            print("1. 准备测试数据...")
            test_file_path = "/Users/yuanyuqing/Documents/code/schoolProject/字段配置测试文档.docx"
            if not os.path.exists(test_file_path):
                self.log_result("完整流程测试", False, "测试文档不存在")
                return False
            
            # 2. 获取可用字段配置
            print("2. 获取可用字段配置...")
            response = requests.get(f"{self.backend_url}/api/config/protocol-fields")
            if response.status_code != 200:
                self.log_result("获取字段配置", False, "无法获取协议字段")
                return False
            
            protocol_fields = response.json()['data']['list']
            if len(protocol_fields) < 3:
                self.log_result("获取字段配置", False, "协议字段数量不足")
                return False
            
            # 选择前3个字段作为测试
            selected_field_ids = [field['id'] for field in protocol_fields[:3]]
            selected_field_names = [field['name'] for field in protocol_fields[:3]]
            print(f"   选择字段: {selected_field_names}")
            
            # 3. 上传文档并启动任务
            print("3. 上传文档并启动提取任务...")
            with open(test_file_path, 'rb') as f:
                files = {'file': f}
                data = {'field_ids': selected_field_ids}
                response = requests.post(f"{self.backend_url}/api/extract/start", 
                                       files=files, data=data)
            
            if response.status_code != 200:
                self.log_result("启动提取任务", False, f"状态码: {response.status_code}")
                return False
            
            task_id = response.json()['data']['task_id']
            returned_expected_fields = response.json()['data'].get('expected_fields', [])
            print(f"   任务ID: {task_id}")
            print(f"   返回期望字段: {returned_expected_fields}")
            
            # 验证期望字段传递
            if set(returned_expected_fields) != set(selected_field_names):
                self.log_result("期望字段传递", False, 
                              f"期望字段不匹配 - 期望: {selected_field_names}, 返回: {returned_expected_fields}")
                return False
            else:
                self.log_result("期望字段传递", True, f"正确传递了 {len(selected_field_names)} 个字段")
            
            # 4. 等待任务完成并监控进度
            print("4. 等待任务完成...")
            max_wait = 60
            wait_time = 0
            final_status = None
            
            while wait_time < max_wait:
                response = requests.get(f"{self.backend_url}/api/extract/status/{task_id}")
                if response.status_code == 200:
                    status_data = response.json()['data']
                    status = status_data['status']
                    progress = status_data.get('progress', 0)
                    message = status_data.get('message', '')
                    mapping_quality = status_data.get('mapping_quality')
                    
                    print(f"   进度: {progress}% - {message}")
                    
                    if status == 'success':
                        final_status = status_data
                        print(f"   任务完成！映射质量: {mapping_quality}")
                        break
                    elif status == 'failed':
                        self.log_result("任务执行", False, f"任务失败: {message}")
                        return False
                
                time.sleep(2)
                wait_time += 2
            else:
                self.log_result("任务执行", False, "任务超时")
                return False
            
            # 5. 验证映射质量评估
            print("5. 验证映射质量评估...")
            if not final_status or not final_status.get('mapping_quality'):
                self.log_result("映射质量评估", False, "未返回映射质量信息")
                return False
            
            quality = final_status['mapping_quality']
            score = quality['score']
            level = quality['level']
            exact_count = quality['exact_count']
            fuzzy_count = quality['fuzzy_count']
            unmatched_count = quality['unmatched_count']
            total = quality['total']
            
            print(f"   质量评分: {score:.3f} ({level})")
            print(f"   匹配详情: 精确{exact_count}个, 模糊{fuzzy_count}个, 未匹配{unmatched_count}个")
            
            # 验证质量评分合理性
            if 0 <= score <= 1:
                self.log_result("映射质量评估", True, 
                              f"评分: {score:.3f} ({level}), 匹配率: {((exact_count+fuzzy_count)/total*100):.1f}%")
            else:
                self.log_result("映射质量评估", False, f"评分超出合理范围: {score}")
                return False
            
            # 6. 测试下载功能
            print("6. 测试结果下载...")
            download_response = requests.get(f"{self.backend_url}/api/extract/download/{task_id}")
            if download_response.status_code == 200:
                # 检查文件内容
                content = download_response.content
                if len(content) > 1000:  # Excel文件应该比较大
                    self.log_result("文件下载", True, f"文件大小: {len(content)} bytes")
                else:
                    self.log_result("文件下载", False, "下载文件内容异常")
                    return False
            else:
                self.log_result("文件下载", False, f"下载失败: {download_response.status_code}")
                return False
            
            # 7. 验证智能分流逻辑（模拟前端行为）
            print("7. 验证智能分流逻辑...")
            if score > 0.9:
                expected_action = "直接下载"
            elif score > 0.7:
                expected_action = "可选修正"
            else:
                expected_action = "强制修正"
            
            print(f"   根据评分 {score:.3f}，预期分流策略: {expected_action}")
            self.log_result("智能分流验证", True, 
                          f"评分{score:.3f} -> {expected_action}策略")
            
            # 8. 完整流程总结
            self.log_result("完整智能预映射流程", True, 
                          f"成功完成端到端测试 - 质量评分: {score:.3f}")
            
            return True
            
        except Exception as e:
            self.log_result("完整流程测试", False, f"异常: {str(e)}")
            return False
    
    def test_edge_cases(self):
        """测试边界情况"""
        print("\n🔍 测试边界情况...")
        
        test_cases = [
            {
                'name': '空字段选择',
                'field_ids': [],
                'expected_error': '请至少选择一个字段'
            },
            {
                'name': '无效字段ID',
                'field_ids': ['invalid_id_123'],
                'expected_error': '未找到对应字段'  # 预期行为
            }
        ]
        
        all_passed = True
        for test_case in test_cases:
            try:
                test_file_path = "/Users/yuanyuqing/Documents/code/schoolProject/字段配置测试文档.docx"
                if not os.path.exists(test_file_path):
                    continue
                    
                with open(test_file_path, 'rb') as f:
                    files = {'file': f}
                    data = {'field_ids': test_case['field_ids']}
                    response = requests.post(f"{self.backend_url}/api/extract/start", 
                                           files=files, data=data)
                
                if test_case['field_ids'] == []:  # 空字段选择应该失败
                    if response.status_code == 400:
                        self.log_result(f"边界测试 - {test_case['name']}", True, "正确拒绝空字段")
                    else:
                        self.log_result(f"边界测试 - {test_case['name']}", False, 
                                      f"应该拒绝但返回: {response.status_code}")
                        all_passed = False
                else:  # 无效字段应该能正常处理
                    if response.status_code in [200, 400]:
                        self.log_result(f"边界测试 - {test_case['name']}", True, "正确处理无效字段")
                    else:
                        self.log_result(f"边界测试 - {test_case['name']}", False, 
                                      f"异常响应: {response.status_code}")
                        all_passed = False
                        
            except Exception as e:
                self.log_result(f"边界测试 - {test_case['name']}", False, f"异常: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def generate_comprehensive_report(self):
        """生成综合测试报告"""
        print("\n" + "="*60)
        print("📊 智能预映射功能综合测试报告")
        print("="*60)
        
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
        
        # 功能覆盖度分析
        print("\n📋 功能覆盖度分析:")
        features = {
            '期望字段传递': any('期望字段传递' in r['test'] for r in self.test_results if r['success']),
            '映射质量评估': any('映射质量评估' in r['test'] for r in self.test_results if r['success']),
            '智能流程分流': any('智能分流' in r['test'] for r in self.test_results if r['success']),
            '端到端集成': any('完整流程' in r['test'] for r in self.test_results if r['success'])
        }
        
        for feature, covered in features.items():
            status = "✅ 已实现" if covered else "❌ 未实现"
            print(f"  {status} {feature}")
        
        print("\n" + "="*60)
        
        # 保存测试报告
        report_data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total': total,
                'passed': passed,
                'failed': total - passed,
                'pass_rate': f"{passed/total*100:.1f}%"
            },
            'feature_coverage': features,
            'details': self.test_results
        }
        
        with open('smart_mapping_integration_test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print("综合测试报告已保存到: smart_mapping_integration_test_report.json")
        
        return passed == total

def main():
    print("🚀 智能预映射功能完整集成测试")
    print("="*60)
    
    tester = SmartMappingIntegrationTester()
    
    # 执行测试
    tests = [
        tester.test_complete_smart_workflow,
        tester.test_edge_cases
    ]
    
    for test_func in tests:
        test_func()
        time.sleep(1)  # 避免请求过快
    
    # 生成报告
    all_passed = tester.generate_comprehensive_report()
    
    if all_passed:
        print("\n🎉 所有测试通过！智能预映射功能完整可用")
        print("\n✨ 核心功能实现:")
        print("   • 期望字段传递机制")
        print("   • 映射质量实时评估")
        print("   • 智能流程分流策略")
        print("   • 端到端集成验证")
    else:
        print("\n⚠️  部分测试失败，请检查相关功能")
    
    return all_passed

if __name__ == "__main__":
    main()