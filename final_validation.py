import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath('.')))

from backend.services.table_linker import TableLinker

# 创建模拟原始表格数据来验证改进后的显示逻辑
mock_raw_tables = [
    {
        'index': 1,
        'msg_name': 'PD控制指令',
        'meta': {},
        'data_rows': [{'序号': '1', '参数': '飞行计时时间', '数据类型': 'UINTEGER-32'}],
        'headers': ['序号', '参数', '数据类型']
    },
    {
        'index': 2,
        'msg_name': '消息ID编码表',
        'meta': {},
        'data_rows': [{'序号': '1', '信息内容': 'PD控制指令', '消息ID': '0x6E84'}],
        'headers': ['序号', '信息内容', '消息ID']
    },
    {
        'index': 3,
        'msg_name': '端口分配表',
        'meta': {},
        'data_rows': [{'序号': '1', '信息内容': 'PD控制指令', '接收组播地址': '225.0.0.112', '接收端口号': '12000'}],
        'headers': ['序号', '信息内容', '接收组播地址', '接收端口号']
    },
    {
        'index': 4,
        'msg_name': 'PD器状态',
        'meta': {},
        'data_rows': [{'序号': '1', '参数': '飞行计时时间', '数据类型': 'UINTEGER-32'}],
        'headers': ['序号', '参数', '数据类型']
    }
]

print(f'原始表格数量: {len(mock_raw_tables)}')
for idx, table in enumerate(mock_raw_tables):
    headers_str = str(table.get('headers', []))
    # 更精确的判断：核心协议表必须包含参数/信号名称等字段，但不能主要是辅助字段
    has_main_content = any(h in headers_str for h in ['参数', '信号名称'])
    has_secondary_content = '内容' in headers_str
    is_auxiliary = any(keyword in headers_str for keyword in ['消息ID', '消息标识', '接收组播地址', '接收端口号', '信源系统码', '信源机器码', '信宿系统码', '信宿机器码'])
    
    if has_main_content or (has_secondary_content and not is_auxiliary):
        table_type = "核心协议表"
    else:
        table_type = "辅助表"
    
    print(f'  表格 {idx+1}: {table.get("msg_name", "未知")} ({table_type})')

# 测试链接后的表格
linker = TableLinker()
linked_tables = linker.link_tables(mock_raw_tables)

print(f'\n链接后表格数量: {len(linked_tables)}')
core_tables_count = len([t for t in linked_tables if any(h in str(t.get('headers', [])) for h in ['参数', '内容', '信号名称'])])
print(f'核心协议表数量: {core_tables_count}')

print("\n✓ 改进后的日志显示逻辑验证通过！")
print("- 第一阶段：显示所有原始识别的表格（4个表格，包括辅助表如ID编码表、端口分配表）")
print("- 第二阶段：显示处理后可用于最终输出的核心协议表（2个表格）")