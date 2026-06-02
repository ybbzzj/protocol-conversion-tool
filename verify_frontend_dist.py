# -*- coding: utf-8 -*-
import os
import re
import sys


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(base_dir, "public", "dist")
    index_path = os.path.join(root, "index.html")

    if not os.path.exists(index_path):
        print("前端 dist 不存在:", index_path)
        return 1

    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()

    refs = re.findall(r"""(?:src|href)=["']/([^"']+)["']""", html)
    asset_refs = [p for p in refs if p.startswith("assets/")]
    missing = [p for p in asset_refs if not os.path.exists(os.path.join(root, p))]

    print("前端资源引用:", len(asset_refs))
    for item in missing:
        print("缺失:", item)

    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
