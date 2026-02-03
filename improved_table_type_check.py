import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath('.')))

# 验证改进后的表格类型判断逻辑
table1 = {'headers': ['序号', '信息内容', '消息ID'], 'msg_name': 'ID编码表'}
table2 = {'headers': ['序号', '信息内容', '接收组播地址', '接收端口号'], 'msg_name': '端口分配表'}
table3 = {'headers': ['序号', '参数', '数据类型'], 'msg_name': 'PD控制指令'}
table4 = {'headers': ['序号', '参数', '数据类型'], 'msg_name': 'PD器状态'}

tables = [table1, table2, table3, table4]

for i, table in enumerate(tables, 1):
    headers_str = str(table.get('headers', []))
    # 更精确的判断：核心协议表必须包含参数/内容/信号名称等字段，但不能主要是辅助字段
    has_main_content = any(h in headers_str for h in ['参数', '信号名称'])
    has_secondary_content = '内容' in headers_str
    is_auxiliary = any(keyword in headers_str for keyword in ['消息ID', '消息标识', '接收组播地址', '接收端口号', '信源系统码', '信源机器码', '信宿系统码', '信宿机器码'])
    
    if has_main_content or (has_secondary_content and not is_auxiliary):
        table_type = "核心协议表"
    else:
        table_type = "辅助表"
    
    print(f'表格{i} ({table["msg_name"]}): {table_type} - headers={table["headers"]}')