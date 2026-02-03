#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试表格检测器是否能正确识别端口分配表和消息ID编码表
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.table_detector import TableDetector
import tempfile
import zipfile
from xml.etree import ElementTree as ET

def create_test_docx():
    """创建一个测试文档，包含端口分配表和消息ID编码表"""
    
    # 创建一个临时目录来构建.docx文件
    temp_dir = tempfile.mkdtemp()
    docx_path = os.path.join(temp_dir, "test_protocol.docx")
    
    # .docx文件实际上是ZIP压缩包，包含XML文件
    # 我们需要创建一个简化版的Word文档结构
    docx_template_dir = os.path.join(temp_dir, "word")
    os.makedirs(docx_template_dir, exist_ok=True)
    
    # 创建一个简化的document.xml
    document_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <!-- 表4 PD控制指令 -->
        <w:tbl>
            <w:tr>
                <w:tc><w:p><w:r><w:t>信息名称</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>PD控制指令</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>上级信息名称</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>—</w:t></w:r></w:p></w:tc>
            </w:tr>
            <w:tr>
                <w:tc><w:p><w:r><w:t>序号</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>参数</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>数据类型</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>数据长度（字节）</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>值域</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>单位</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>备注</w:t></w:r></w:p></w:tc>
            </w:tr>
            <w:tr>
                <w:tc><w:p><w:r><w:t>1</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>飞行计时时间</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>UINTEGER-32</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>4</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>0~0xFFFFFFFF</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>ms</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>接收XX指令后，完成时标清零</w:t></w:r></w:p></w:tc>
            </w:tr>
            <w:tr>
                <w:tc><w:p><w:r><w:t>2</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>控制指令1</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>USHORT</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>2</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>0x1701：供电\n0x1702：断电\n其他值无效</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>—</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t></w:t></w:r></w:p></w:tc>
            </w:tr>
        </w:tbl>
        
        <!-- 表2 消息ID编码表 -->
        <w:tbl>
            <w:tr>
                <w:tc><w:p><w:r><w:t>表2 消息ID编码表</w:t></w:r></w:p></w:tc>
            </w:tr>
            <w:tr>
                <w:tc><w:p><w:r><w:t>序号</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>信源</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>信宿</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>信息内容</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>消息ID</w:t></w:r></w:p></w:tc>
            </w:tr>
            <w:tr>
                <w:tc><w:p><w:r><w:t>1</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t></w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>XX组合计算模块</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>PD控制指令</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>0x6E84</w:t></w:r></w:p></w:tc>
            </w:tr>
            <w:tr>
                <w:tc><w:p><w:r><w:t>2</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t></w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>XX装置</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>PD控制指令</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>0x81A0</w:t></w:r></w:p></w:tc>
            </w:tr>
            <w:tr>
                <w:tc><w:p><w:r><w:t>3</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t></w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>XX模块</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>PD器状态</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>0x7000</w:t></w:r></w:p></w:tc>
            </w:tr>
        </w:tbl>
        
        <!-- 表1 端口分配表 -->
        <w:tbl>
            <w:tr>
                <w:tc><w:p><w:r><w:t>表1 端口分配表</w:t></w:r></w:p></w:tc>
            </w:tr>
            <w:tr>
                <w:tc><w:p><w:r><w:t>序号</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>信源</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>信宿</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>信息内容</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>接收组播地址</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>接收端口号</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>信源系统码</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>信源机器码</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>信宿系统码</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>信宿机器码</w:t></w:r></w:p></w:tc>
            </w:tr>
            <w:tr>
                <w:tc><w:p><w:r><w:t>1</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t></w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>XX组合计算模块</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>PD控制指令</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>225.0.0.112</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>12000</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>100</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>110</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>100</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>112</w:t></w:r></w:p></w:tc>
            </w:tr>
            <w:tr>
                <w:tc><w:p><w:r><w:t>2</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t></w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>XX装置</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>PD控制指令</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>225.0.0.112</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>12000</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>100</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>129</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>100</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>112</w:t></w:r></w:p></w:tc>
            </w:tr>
            <w:tr>
                <w:tc><w:p><w:r><w:t>3</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t></w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>XX模块</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>PD器状态</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>225.0.0.105</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>20000</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>100</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>112</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>0</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>0</w:t></w:r></w:p></w:tc>
            </w:tr>
        </w:tbl>
    </w:body>
</w:document>'''

    with open(os.path.join(docx_template_dir, "document.xml"), "w", encoding="utf-8") as f:
        f.write(document_xml)
    
    # 创建其他必需的文件
    rels_dir = os.path.join(temp_dir, "_rels")
    os.makedirs(rels_dir, exist_ok=True)
    
    rels_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''
    
    with open(os.path.join(rels_dir, ".rels"), "w", encoding="utf-8") as f:
        f.write(rels_xml)
    
    # 创建word/_rels目录
    word_rels_dir = os.path.join(docx_template_dir, "_rels")
    os.makedirs(word_rels_dir, exist_ok=True)
    
    word_rels_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>'''
    
    with open(os.path.join(word_rels_dir, "document.xml.rels"), "w", encoding="utf-8") as f:
        f.write(word_rels_xml)
    
    # 创建[Content_Types].xml
    content_types_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>'''
    
    with open(os.path.join(temp_dir, "[Content_Types].xml"), "w", encoding="utf-8") as f:
        f.write(content_types_xml)
    
    # 创建样式文件
    styles_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
</w:styles>'''
    
    with open(os.path.join(docx_template_dir, "styles.xml"), "w", encoding="utf-8") as f:
        f.write(styles_xml)
    
    # 将目录打包成ZIP文件并重命名为.docx
    with zipfile.ZipFile(docx_path, 'w') as zipf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file != "test_protocol.docx":  # 不包含自己
                    file_path = os.path.join(root, file)
                    arc_path = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arc_path)
    
    return docx_path

def test_table_detection():
    """测试表格检测功能"""
    print("创建测试文档...")
    test_docx_path = create_test_docx()
    
    print(f"测试文档已创建: {test_docx_path}")
    
    # 使用TableDetector测试
    detector = TableDetector()
    try:
        print("开始检测表格...")
        result = detector.extract_tables_from_docx(test_docx_path)
        
        print(f"检测到 {len(result)} 个表格:")
        
        for i, table in enumerate(result):
            print(f"\n表格 {i+1}:")
            print(f"  消息名称: {table.get('msg_name', 'N/A')}")
            print(f"  表格索引: {table.get('index', 'N/A')}")
            print(f"  表头: {table.get('headers', [])}")
            print(f"  数据行数: {len(table.get('data_rows', []))}")
            print(f"  元数据: {table.get('meta', {})}")
            
            # 检查是否识别到了端口分配表或消息ID编码表
            headers_str = ' '.join(table.get('headers', []))
            if '接收组播地址' in headers_str or '接收端口号' in headers_str:
                print(f"  → 识别为: 端口分配表")
            elif '消息ID' in headers_str:
                print(f"  → 识别为: 消息ID编码表")
            elif '参数' in headers_str and '数据类型' in headers_str:
                print(f"  → 识别为: 协议参数表")
            else:
                print(f"  → 识别为: 其他类型表格")
        
        # 统计识别结果
        port_tables = 0
        id_tables = 0
        protocol_tables = 0
        other_tables = 0
        
        for table in result:
            headers_str = ' '.join(table.get('headers', []))
            if '接收组播地址' in headers_str or '接收端口号' in headers_str:
                port_tables += 1
            elif '消息ID' in headers_str:
                id_tables += 1
            elif '参数' in headers_str and '数据类型' in headers_str:
                protocol_tables += 1
            else:
                other_tables += 1
        
        print(f"\n识别统计:")
        print(f"  端口分配表: {port_tables}")
        print(f"  消息ID编码表: {id_tables}")
        print(f"  协议参数表: {protocol_tables}")
        print(f"  其他表格: {other_tables}")
        
        # 检查是否成功识别到了关键表格
        if port_tables > 0 and id_tables > 0:
            print("\n✓ 成功识别到端口分配表和消息ID编码表!")
            return True
        else:
            print("\n✗ 未能正确识别端口分配表和消息ID编码表")
            return False
        
    except Exception as e:
        print(f"检测过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理临时文件
        import shutil
        temp_dir = os.path.dirname(test_docx_path)
        try:
            shutil.rmtree(temp_dir)
        except:
            pass  # 忽略清理错误

if __name__ == "__main__":
    success = test_table_detection()
    if success:
        print("\n表格检测功能测试通过!")
    else:
        print("\n表格检测功能测试失败!")