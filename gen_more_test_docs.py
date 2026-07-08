# -*- coding: utf-8 -*-
"""
扩充"不常见表头"测试文档集 —— 仅用于验证【配置兜底】通道。

设计要点（全表头不含标准关键词 内容/参数/类型/序号/字节/长度/单位/值，
   仅 A 型表头保留一个 phase1 候选扫描词"说明"以便 phase1 找到候选行）：

1. 多词表家族：货号/品名/型号、编码/物料/属性/描述、项次/品项/规范/注解、
   卡号/标签/维度/范畴、代号/指标/区间 等
2. 不同列数：3 列(测 ≥3 绝对数量兜底)、4 列、8 列(测比例稀释)
3. 不同匹配率：100% / 75% / 67% / 60% 应过；50% / 33% / 25% 应拦
4. A 型多行表头也覆盖

判据：表是否真正被提取进 result['tables'] 且 table_type=='field_def'
"""
import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from docx import Document
from backend.services.table_detector import DocumentParser

logging.basicConfig(level=logging.WARNING, format='[%(name)s] %(message)s')

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_docs')
os.makedirs(OUT_DIR, exist_ok=True)


def make_bc(tag, header_cols, data_rows=2):
    doc = Document()
    doc.add_paragraph(f'测试表 {tag}')
    t = doc.add_table(rows=data_rows + 1, cols=len(header_cols))
    for j, h in enumerate(header_cols):
        t.rows[0].cells[j].text = h
    for r in range(1, data_rows + 1):
        for j in range(len(header_cols)):
            t.rows[r].cells[j].text = f'值{r}-{j}'
    path = os.path.join(OUT_DIR, f'uncommon_{tag}.docx')
    doc.save(path)
    return path


def make_a(tag, header_cols, data_rows=2):
    doc = Document()
    doc.add_paragraph(f'测试表 {tag}')
    n = 2 + 1 + data_rows
    t = doc.add_table(rows=n, cols=len(header_cols))
    meta0 = ['通信帧名称', '某信息', '信息标识', '0x9F'] + [''] * (len(header_cols) - 4)
    meta1 = ['信息流向', 'A→B', '发送周期', '100ms'] + [''] * (len(header_cols) - 4)
    for j, v in enumerate(meta0):
        t.rows[0].cells[j].text = v
    for j, v in enumerate(meta1):
        t.rows[1].cells[j].text = v
    for j, h in enumerate(header_cols):
        t.rows[2].cells[j].text = h
    for r in range(3, n):
        for j in range(len(header_cols)):
            t.rows[r].cells[j].text = f'值{r}-{j}'
    path = os.path.join(OUT_DIR, f'uncommon_{tag}.docx')
    doc.save(path)
    return path


def verify(path, config_fields, expect_pass, desc):
    cfg = [{'table_type': 'field_def', 'required_fields': list(config_fields)}]
    p = DocumentParser(config=cfg)
    res = p.parse(path)
    ok = any(t.get('table_type') == 'field_def' for t in res['tables'])
    hit = ok == expect_pass
    mark = '✅' if ok else '❌'
    flag = 'OK' if hit else '✗MISMATCH'
    print(f'  {mark} [{flag}] {desc}  (提取={"是" if ok else "否"}, 期望={"过" if expect_pass else "拦"})')
    return hit


def main():
    print(f'扩充生成测试文档到: {OUT_DIR}\n')
    cases = [
        # ---- 3 列小表：测试 ≥3 绝对数量 与 60% 边界 ----
        ('s3_full', make_bc('s3_full', ['货号', '品名', '型号']),
         ['货号', '品名', '型号'], True, '3列全命中(100%)'),
        ('s3_two', make_bc('s3_two', ['货号', '品名', '型号']),
         ['货号', '品名'], False, '3列命中2(67%)→仅2命中<3,phase2拦(实际)'),
        ('s3_one', make_bc('s3_one', ['货号', '品名', '型号']),
         ['货号'], False, '3列命中1(33%)→拦(比例与数量都不够)'),

        # ---- 4 列：新词表 编码/物料/属性/描述 ----
        ('c4_75', make_bc('c4_75', ['编码', '物料', '属性', '描述']),
         ['编码', '物料', '属性'], True, '4列命中3(75%)'),
        ('c4_50', make_bc('c4_50', ['编码', '物料', '属性', '描述']),
         ['编码', '物料'], False, '4列命中2(50%)→拦'),

        # ---- 8 列大表：测试比例稀释 + ≥3 绝对数量兜底 ----
        ('b8_three', make_bc('b8_three', ['项次', '品项', '规范', '注解',
                                          '类别', '等级', '来源', '状态']),
         ['项次', '品项', '规范'], False, '8列命中3(37.5%)→命中率<60%,phase2拦'),
        ('b8_two', make_bc('b8_two', ['项次', '品项', '规范', '注解',
                                      '类别', '等级', '来源', '状态']),
         ['项次', '品项'], False, '8列命中2(25%)→拦(<3且比例低)'),
        ('b8_six', make_bc('b8_six', ['项次', '品项', '规范', '注解',
                                      '类别', '等级', '来源', '状态']),
         ['项次', '品项', '规范', '注解', '类别', '等级'], True, '8列命中6(75%)'),

        # ---- 6 列：卡号/标签/维度/范畴 词表 ----
        ('k6_60', make_bc('k6_60', ['卡号', '标签', '维度', '范畴', '阈值', '状态']),
         ['卡号', '标签', '维度'], False, '6列命中3(50%)→命中率<60%,phase2拦'),
        ('k6_67', make_bc('k6_67', ['卡号', '标签', '维度', '范畴', '阈值', '状态']),
         ['卡号', '标签', '维度', '范畴'], True, '6列命中4(67%)'),

        # ---- A 型多行表头（含候选词"说明"）----
        ('a8_62', make_a('a8_62', ['代号', '指标', '区间', '说明', '来源', '上限', '下限', '状态']),
         ['代号', '指标', '区间', '说明', '来源'], True, 'A型8列命中5(62.5%)'),
        ('a6_50', make_a('a6_50', ['代号', '指标', '区间', '说明', '来源', '状态']),
         ['代号', '指标'], False, 'A型6列命中2(33%)→拦'),
        ('a5_100', make_a('a5_100', ['编码', '物料', '属性', '描述', '说明']),
         ['编码', '物料', '属性', '描述', '说明'], True, 'A型5列全命中(100%)'),
    ]

    all_ok = True
    for tag, path, cfg, expect, desc in cases:
        print(f'文档: {os.path.basename(path)}  ({desc})')
        all_ok = verify(path, cfg, expect, desc) and all_ok
    print('\n' + ('全部符合预期 ✅' if all_ok else '存在不符合预期的用例 ❌'))


if __name__ == '__main__':
    main()
