from backend.services.table_detector import DocumentParser
import json

def test_new_parser():
    file_path = "协议模板（公开）.docx"
    parser = DocumentParser()
    result = parser.parse(file_path)
    
    print(f"Total tables found: {result['tables_count']}")
    for i, table in enumerate(result['tables']):
        print(f"\n--- Table {i} ---")
        print(f"Message Name: {table['msg_name']}")
        print(f"Meta: {table['meta']}")
        print(f"Headers: {table['headers']}")
        print(f"Data Rows Count: {len(table['data_rows'])}")
        if table['data_rows']:
            print(f"First Data Row: {table['data_rows'][0]}")

if __name__ == "__main__":
    test_new_parser()
