# 分析测试文档中的表格结构
from docx2python import docx2python

def analyze_document():
    doc = docx2python('word/测试协议20251216.docx')
    
    print("===测试文档表格分析 ===\n")
    
    #收所有表格的表头信息
    table_headers = []
    protocol_fields = set()
    target_fields = set()
    
    for i, table in enumerate(doc.body):
        print(f"表格 {i}:")
        try:
            #打表格内容用于分析
            if isinstance(table, list) and len(table) > 0:
                # 如果是多维列表，尝试获取表头行
                if isinstance(table[0], list) and len(table[0]) > 0:
                    header_row = table[0]
                    if isinstance(header_row[0], list) and len(header_row[0]) > 0:
                        #处三层嵌套结构
                        headers = []
                        for cell in header_row[0]:
                            if isinstance(cell, list) and len(cell) > 0:
                                #取文本内容
                                content = cell[0]
                                if isinstance(content, str) and content.strip():
                                    headers.append(content.strip())
                        if headers:
                            table_headers.append((i, headers))
                            print(f" 表头: {headers}")
                            #收所有字段名
                            for header in headers:
                                if header and not header.startswith(('[', '(', '•', '-')) and len(header) > 1:
                                    protocol_fields.add(header)
                elif isinstance(table[0], str):
                    #处理字符串格式
                    print(f" 内容: {str(table[0])[:100]}...")
            print()
        except Exception as e:
            print(f" 错误分析表格 {i}: {e}")
    
    print("=== 分析结果 ===")
    print(f"发现的表格数量: {len(table_headers)}")
    print(f"唯一字段名数量: {len(protocol_fields)}")
    
    # 分析字段分布
    field_count = {}
    for field in protocol_fields:
        if len(field) > 1 and not field.isdigit():
            field_count[field] = field_count.get(field, 0) + 1
    
    # 按频率排序
    sorted_fields = sorted(field_count.items(), key=lambda x: x[1], reverse=True)
    print(f"\n高频字段（出现次数>=2）:")
    for field, count in sorted_fields:
        if count >= 2:
            print(f"  {field}: {count}次")
    
    # 生成字段配置JSON
    protocol_fields_config = []
    for field in sorted(list(protocol_fields)):
        if len(field) > 1 and field not in ['', ' ', '\n', '\t'] and not field[0].isdigit():
            # 生成规范化的ID
            field_id = field.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_')
            #清理特殊字符
            field_id = ''.join(c for c in field_id if c.isalnum() or c == '_')
            protocol_fields_config.append({
                "id": f"pf_{field_id}" if not field_id.startswith('pf_') else field_id,
                "name": field
            })
    
    #的目标字段
    target_fields_config = [
        {"id": "tf_id", "name": "ID"},
        {"id": "tf_content", "name": "内容"},
        {"id": "tf_data_type", "name": "数据类型"},
        {"id": "tf_signal_name", "name": "信号名称"},
        {"id": "tf_byte_count", "name": "字节数"},
        {"id": "tf_conversion_type", "name": "转换类型"},
        {"id": "tf_source_code", "name": "信源码"},
        {"id": "tf_dest_code", "name": "信宿码"},
        {"id": "tf_unit", "name": "单位"},
        {"id": "tf_value_range", "name": "取值范围"}
    ]
    
    print("\n===的字段配置 ===")
    print(f"协议字段数量: {len(protocol_fields_config)}")
    print(f"目标字段数量: {len(target_fields_config)}")
    
    print("\n=== 示例字段 (前10个) ===")
    for field_config in protocol_fields_config[:10]:
        print(f"  {field_config['name']}: {field_config['id']}")
        
    print("\n===JSON内容====");
    import json
    config = {
        "protocolFields": protocol_fields_config,
        "targetFields": target_fields_config
    }
    print(json.dumps(config, ensure_ascii=False, indent=2))
    
    # 保存到文件
    with open('测试文档字段配置.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print("\n配置已保存到:测试文档字段配置.json")

if __name__ == "__main__":
    analyze_document()