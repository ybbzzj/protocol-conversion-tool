import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath('.')))

# 模拟原始表格数据来验证最终格式
raw_tables = [
    {
        'msg_name': '端口分配表',
        'headers': ['序号', '信源', '信宿', '信息内容', '接收组播地址', '接收端口号'],
        'data_rows': [
            {
                '序号': '1',
                '信源': 'XX组合计算模块',
                '信宿': 'PD控制指令',
                '信息内容': 'PD控制指令',
                '接收组播地址': '225.0.0.112',
                '接收端口号': '12000'
            }
        ]
    }
]

# 分类原始表格：辅助表（不会输出到结果）和核心表（会输出到结果）
auxiliary_tables = []
core_tables = []

for table in raw_tables:
    headers_str = str(table.get('headers', []))
    has_main_content = any(h in headers_str for h in ['参数', '信号名称'])
    has_secondary_content = '内容' in headers_str
    is_auxiliary = any(keyword in headers_str for keyword in ['消息ID', '消息标识', '接收组播地址', '接收端口号', '信源系统码', '信源机器码', '信宿系统码', '信宿机器码'])
    
    if has_main_content or (has_secondary_content and not is_auxiliary):
        core_tables.append(table)
    else:
        auxiliary_tables.append(table)

print('>>> 不会输出到结果的表格 <<<')
for idx, table in enumerate(auxiliary_tables):
    msg_id = table.get('msg_name', '未知消息')
    print(f'\n>>> [辅助表] 展示原始表格内容 [消息: {msg_id}] <<<')
    
    # 打印表头
    headers = table.get('headers', [])
    if headers:
        headers_str = ' | '.join(headers)
        print(f'  [表头] {headers_str}')
    
    # 打印原始数据行
    print('  [原始数据行]')
    data_rows = table.get('data_rows', [])
    for i, row in enumerate(data_rows):
        row_display = ' | '.join([f"{k}:{v}" for k, v in row.items()])
        print(f'    [{i+1:2d}] {row_display} => ✓ 保留')

print('\n>>> 只显示不会输出到结果的表格部分 <<<')
print('>>> 会输出到结果的表格部分已省略（由后续详细日志记录）<<<')