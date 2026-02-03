import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath('.')))

from backend.services.table_linker import TableLinker

# 创建模拟原始表格数据来验证改进后的显示逻辑
mock_raw_tables = [
    {
        'index': 1,
        'msg_name': '端口分配表',
        'meta': {'接收组播地址': '225.0.0.112', '接收端口号': '12000'},
        'data_rows': [{'序号': '1', '信息内容': 'PD控制指令', '接收组播地址': '225.0.0.112', '接收端口号': '12000'}],
        'headers': ['序号', '信息内容', '接收组播地址', '接收端口号']
    },
    {
        'index': 2,
        'msg_name': 'ID编码表',
        'meta': {},
        'data_rows': [{'序号': '1', '信息内容': 'PD控制指令', '消息ID': '0x6E84'}],
        'headers': ['序号', '信息内容', '消息ID']
    },
    {
        'index': 3,
        'msg_name': 'PD控制指令',
        'meta': {},
        'data_rows': [{'序号': '1', '参数': '飞行计时时间', '数据类型': 'UINTEGER-32'}],
        'headers': ['序号', '参数', '数据类型']
    },
    {
        'index': 4,
        'msg_name': 'PD器状态',
        'meta': {},
        'data_rows': [{'序号': '1', '参数': '飞行计时时间', '数据类型': 'UINTEGER-32'}],
        'headers': ['序号', '参数', '数据类型']
    }
]

print('>>> 详细识别信息 <<<')
for idx, table in enumerate(mock_raw_tables):
    # 判断类型
    headers_str = str(table.get('headers', []))
    has_main_content = any(h in headers_str for h in ['参数', '信号名称'])
    has_secondary_content = '内容' in headers_str
    is_auxiliary = any(keyword in headers_str for keyword in ['消息ID', '消息标识', '接收组播地址', '接收端口号', '信源系统码', '信源机器码', '信宿系统码', '信宿机器码'])
    
    if has_main_content or (has_secondary_content and not is_auxiliary):
        table_type = '核心协议表'
    else:
        table_type = '辅助表'
    
    print(f'  [表格 {idx+1}: {table.get("msg_name", "未知")}]')
    print(f'    类型: {table_type}')
    print(f'    表头: {table.get("headers", [])}')
    print(f'    数据行数: {len(table.get("data_rows", []))}')
    if table.get('meta'):
        print(f'    元数据: {table["meta"]}')
    print()  # 空行分隔