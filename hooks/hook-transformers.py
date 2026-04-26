# -*- coding: utf-8 -*-
"""
Local PyInstaller hook for transformers.

Purpose:
- Override problematic contrib hook that may fail on Python 3.8
  when probing `dataclasses.__version__`.
- Keep packaging behavior simple and robust for offline builds.
"""

from PyInstaller.utils.hooks import collect_all, copy_metadata


datas, binaries, hiddenimports = collect_all("transformers")
# 递归拷贝 metadata，避免运行时缺少依赖分发信息（如 regex）
datas += copy_metadata("transformers", recursive=True)
