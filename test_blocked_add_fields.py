# -*- coding: utf-8 -*-
"""
验证"被拦住的表，如果加了不常见字段还会被拦住吗？"

方法：对每个之前被拦的文档
  1) 原配置（只配部分列）→ 确认仍被拦
  2) 把表头所有列都加进配置（100% 覆盖）→ 验证通过
  3) 再测"刚好跨过门槛"的最小加法（≥3 命中 且 比率≥60%）
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


def read_header(path):
    doc = Document(path)
    for t in doc.tables:
        rows = [[c.text.strip() for c in r.cells] for r in t.rows]
        # A 型表：行0/1 是元数据，真实字段表头在行2
        if rows and any('通信帧名称' in c or '信息标识' in c for c in rows[0]):
            if len(rows) > 2:
                return [c for c in rows[2] if c]
            return []
        # B/C 型：行0 即表头
        if rows and any(rows[0]):
            return [c for c in rows[0] if c]
    return []


def parse_with(path, config_fields):
    cfg = [{'table_type': 'field_def', 'required_fields': list(config_fields)}]
    p = DocumentParser(config=cfg)
    res = p.parse(path)
    return any(t.get('table_type') == 'field_def' for t in res['tables'])


def main():
    # (文档, 原被拦配置)
    blocked = [
        ('uncommon_s3_two.docx', ['货号', '品名']),
        ('uncommon_s3_one.docx', ['货号']),
        ('uncommon_c4_50.docx', ['编码', '物料']),
        ('uncommon_b8_three.docx', ['项次', '品项', '规范']),
        ('uncommon_b8_two.docx', ['项次', '品项']),
        ('uncommon_k6_60.docx', ['卡号', '标签', '维度']),
        ('uncommon_a6_50.docx', ['代号', '指标']),
    ]

    all_ok = True
    for fname, blocked_cfg in blocked:
        path = os.path.join(OUT_DIR, fname)
        header = read_header(path)
        full_cfg = list(header)  # 100% 覆盖

        still_blocked = not parse_with(path, blocked_cfg)
        passes_full = parse_with(path, full_cfg)

        # 最小加法：从被拦配置开始，逐个补表头列，直到刚跨过门槛
        minimal = list(blocked_cfg)
        for col in header:
            if col not in minimal:
                minimal.append(col)
                m = len([c for c in header if c in minimal])
                if m >= 3 and m / len(header) >= 0.6:
                    break
        passes_min = parse_with(path, minimal)

        ok = still_blocked and passes_full and passes_min
        all_ok = all_ok and ok
        print(f'文档: {fname}')
        print(f'   表头({len(header)}列): {header}')
        print(f'   原配置{blocked_cfg} → {"❌被拦" if still_blocked else "⚠️竟通过了(异常)"}')
        print(f'   加全部字段{len(full_cfg)}个 → {"✅通过" if passes_full else "❌仍拦(异常)"} (100%覆盖)')
        print(f'   最小加法{len(minimal)}个 → {"✅通过" if passes_min else "❌仍拦(异常)"} (命中{len([c for c in header if c in minimal])}/{len(header)})')
        print(f'   => {"符合预期 ✅" if ok else "不符合预期 ❌"}')
        print()

    print('=' * 60)
    print('结论：被拦的表，把不常见字段加进配置后【都不再被拦】' if all_ok
          else '存在异常用例 ❌')


if __name__ == '__main__':
    main()
