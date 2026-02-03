import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath('.')))

# 验证表格类型判断逻辑
table1 = {'headers': ['序号', '信息内容', '消息ID'], 'msg_name': 'ID编码表'}
table2 = {'headers': ['序号', '信息内容', '接收组播地址', '接收端口号'], 'msg_name': '端口分配表'}
table3 = {'headers': ['序号', '参数', '数据类型'], 'msg_name': 'PD控制指令'}
table4 = {'headers': ['序号', '参数', '数据类型'], 'msg_name': 'PD器状态'}

tables = [table1, table2, table3, table4]

for i, table in enumerate(tables, 1):
    table_type = '核心协议表' if table.get('headers') and any(h in str(table['headers']) for h in ['参数', '内容', '信号名称']) else '辅助表'
    print(f'表格{i} ({table["msg_name"]}): {table_type} - headers={table["headers"]}')