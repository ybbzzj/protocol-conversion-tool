from docx2python import docx2python
import json

def analyze_with_docx2python(file_path):
    with docx2python(file_path) as doc:
        # doc.body is a list of tables
        # Each table is a list of rows
        # Each row is a list of cells
        # Each cell is a list of paragraphs
        print(f"Number of tables (in body): {len(doc.body)}")
        for i, table in enumerate(doc.body):
            print(f"\nTable {i}:")
            for r_idx, row in enumerate(table[:5]):
                # Flatten the list of paragraphs in each cell
                cells = [" ".join(cell).strip() for cell in row]
                print(f"  Row {r_idx}: {cells}")

analyze_with_docx2python("协议模板（公开）.docx")
