import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath('.')))

try:
    from backend.services.table_detector import DocumentParser
    print('导入成功！')
    
    # 检查是否存在协议文档
    doc_path = os.path.join(os.getcwd(), '协议模板（公开）.docx')
    if os.path.exists(doc_path):
        print(f'找到文档: {doc_path}')
        parser = DocumentParser()
        result = parser.parse(doc_path)
        print(f'解析成功！识别到 {len(result["tables"])} 个表格')
    else:
        print('文档不存在，跳过解析测试')
        docx_files = [f for f in os.listdir('.') if f.endswith('.docx')]
        print('当前目录docx文件:', docx_files)
except Exception as e:
    print(f'错误: {e}')
    import traceback
    traceback.print_exc()