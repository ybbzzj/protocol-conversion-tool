import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath('.')))

# 模拟原始表格数据来验证格式
raw_tables = [
    {
        'msg_name': 'PD控制指令',
        'headers': ['序号', '参数', '数据类型', '数据长度（字节）', '值域', '单位', '备注'],
        'data_rows': [
            {
                '序号': '1',
                '参数': '飞行计时时间',
                '数据类型': 'UINTEGER-32',
                '数据长度（字节）': '4',
                '值域': '0~0xFFFFFFFF',
                '单位': 'ms',
                '备注': '接收XX指令后，完成时标清零'
            },
            {
                '序号': '2',
                '参数': '控制指令1',
                '数据类型': 'USHORT',
                '数据长度（字节）': '2',
                '值域': '0x1701：供电 0x1702：断电 其他值无效',
                '单位': '—',
                '备注': ''
            }
        ]
    }
]

print('>>> 真正原始表格信息 <<<')
for idx, table in enumerate(raw_tables):
    msg_id = table.get('msg_name', '未知消息')
    print(f'\n>>> 展示原始表格内容 [消息: {msg_id}] <<<')
    
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
        print(f'    [{i+1:2d}] {row_display}')
    
    print()  # 空行分隔