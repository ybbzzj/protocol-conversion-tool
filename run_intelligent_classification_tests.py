#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能分类功能全面测试与对比报告
测试场景 A：枚举值与转换公式的智能区分
测试场景 B：备注内容的智能分割与归类
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.data_cleaner import DataProcessor
from comprehensive_test_dataset import ALL_TEST_CASES, get_test_statistics
from datetime import datetime

class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.processor = DataProcessor()
        self.results = []
        
    def run_single_test(self, test_case):
        """运行单个测试用例"""
        name = test_case['name']
        input_data = test_case['input']
        expected = test_case['expected']
        
        # 执行处理
        result = self.processor.process_row(input_data)
        
        # 提取实际结果
        actual = {
            '值域': result['formatted'].get('值域'),
            '单位': result['formatted'].get('单位'),
            '转换公式': result['formatted'].get('转换公式'),
            '备注': result['cleaned'].get('备注')
        }
        
        # 对比结果
        passed = True
        details = []
        
        for key in ['值域', '单位', '转换公式', '备注']:
            exp_val = expected.get(key)
            act_val = actual.get(key)
            
            # 特殊处理 None 和空字符串
            if exp_val is None and (act_val == '' or act_val is None):
                match = True
            elif exp_val == '' and (act_val == '' or act_val is None):
                match = True
            else:
                match = (exp_val == act_val)
            
            if not match:
                passed = False
                details.append({
                    'field': key,
                    'expected': exp_val,
                    'actual': act_val,
                    'match': match
                })
        
        return {
            'name': name,
            'passed': passed,
            'details': details,
            'input': input_data,
            'expected': expected,
            'actual': actual
        }
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 80)
        print("开始运行智能分类功能测试")
        print("=" * 80)
        print()
        
        self.results = []
        for i, test_case in enumerate(ALL_TEST_CASES, 1):
            result = self.run_single_test(test_case)
            self.results.append(result)
            
            # 实时反馈
            status = "PASS" if result['passed'] else "FAIL"
            print(f"[{i}/{len(ALL_TEST_CASES)}] {status} {test_case['name']}")
            
            if not result['passed']:
                for detail in result['details']:
                    print(f"      {detail['field']}:")
                    print(f"        期望：{detail['expected']}")
                    print(f"        实际：{detail['actual']}")
        
        print()
        return self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r['passed'])
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        # 按类别统计
        category_stats = {}
        for result in self.results:
            # 简单分类：根据测试名称判断
            name = result['name'].lower()
            if '枚举' in name:
                category = '枚举值测试'
            elif '混合' in name or '单位' in name or '范围' in name:
                category = '混合内容分割'
            elif '公式' in name or '转换' in name:
                category = '转换公式识别'
            elif '边界' in name or '实际' in name:
                category = '其他'
            else:
                category = '未分类'
            
            if category not in category_stats:
                category_stats[category] = {'total': 0, 'passed': 0}
            category_stats[category]['total'] += 1
            if result['passed']:
                category_stats[category]['passed'] += 1
        
        # 打印报告
        print("\n" + "=" * 80)
        print("📊 智能分类功能测试报告")
        print("=" * 80)
        print(f"测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"测试总数：{total}")
        print(f"通过数量：{passed} ✅")
        print(f"失败数量：{failed} ❌")
        print(f"通过率：{pass_rate:.1f}%")
        print()
        
        print("📈 各类别测试结果:")
        print("-" * 80)
        for category, stats in sorted(category_stats.items()):
            cat_pass_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            bar = "█" * int(cat_pass_rate / 5) + "░" * (20 - int(cat_pass_rate / 5))
            print(f"{category:15s} [{bar}] {stats['passed']:3d}/{stats['total']:3d} ({cat_pass_rate:5.1f}%)")
        print()
        
        # 详细列出失败的测试
        if failed > 0:
            print("❌ 失败测试用例详情:")
            print("-" * 80)
            for result in self.results:
                if not result['passed']:
                    print(f"\n测试：{result['name']}")
                    print(f"输入：{result['input']}")
                    for detail in result['details']:
                        print(f"  字段：{detail['field']}")
                        print(f"    期望：{repr(detail['expected'])}")
                        print(f"    实际：{repr(detail['actual'])}")
            print()
        
        # 典型成功案例展示
        print("\n✅ 典型成功案例展示:")
        print("-" * 80)
        success_examples = [r for r in self.results if r['passed']][:5]
        for example in success_examples:
            print(f"\n测试：{example['name']}")
            print(f"输入备注：{example['input'].get('备注', 'N/A')}")
            if example['actual']['值域']:
                print(f"  → 值域：{example['actual']['值域']}")
            if example['actual']['单位']:
                print(f"  → 单位：{example['actual']['单位']}")
            if example['actual']['转换公式']:
                print(f"  → 转换公式：{example['actual']['转换公式']}")
            if example['actual']['备注']:
                print(f"  → 备注：{example['actual']['备注']}")
        
        print("\n" + "=" * 80)
        print("测试报告结束")
        print("=" * 80)
        
        # 返回统计信息
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': pass_rate,
            'category_stats': category_stats,
            'results': self.results
        }


def main():
    """主函数"""
    runner = TestRunner()
    report = runner.run_all_tests()
    
    # 保存报告到文件
    report_file = os.path.join(os.path.dirname(__file__), 
                               f'test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("智能分类功能测试报告\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"测试总数：{report['total']}\n")
        f.write(f"通过数量：{report['passed']}\n")
        f.write(f"失败数量：{report['failed']}\n")
        f.write(f"通过率：{report['pass_rate']:.1f}%\n\n")
        
        f.write("各类别测试结果:\n")
        f.write("-" * 80 + "\n")
        for category, stats in sorted(report['category_stats'].items()):
            cat_pass_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            f.write(f"{category:15s} {stats['passed']:3d}/{stats['total']:3d} ({cat_pass_rate:5.1f}%)\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("完整测试结果见控制台输出\n")
        f.write("=" * 80 + "\n")
    
    print(f"\n📄 测试报告已保存到：{report_file}")
    
    return 0 if report['passed'] == report['total'] else 1


if __name__ == "__main__":
    sys.exit(main())
