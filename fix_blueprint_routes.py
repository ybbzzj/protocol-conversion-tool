#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复所有 Flask 蓝图路由定义
问题: 蓝图用 url_prefix='/api' 注册，但路由中仍包含完整路径前缀
结果: /api/extract/extract/start 而不是 /api/extract/start

解决: 从蓝图路由中移除重复的前缀部分
"""

import os
import re

# 蓝图与对应的路由前缀映射
blueprint_mappings = {
    'extract.py': 'extract',      # /extract/* -> /*
    'dashboard.py': 'dashboard',  # /dashboard/* -> /*
    'knowledge.py': 'knowledge',  # /knowledge/* -> /*
    'match.py': 'match',          # /match/* -> /*
    'batch.py': 'batch',          # /batch/* -> /*
    'config.py': 'config',        # /config/* -> /*
    'templates.py': 'templates',  # /templates/* -> /*
    'history.py': 'history',      # /history/* -> /*
}

routes_dir = '/Users/yuanyuqing/Documents/code/schoolProject/backend/routes'

def fix_blueprint_routes(filepath, prefix_to_remove):
    """修复蓝图文件中的路由定义"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 找到蓝图名称 (通常是 {name}_bp)
    bp_names = re.findall(r'(\w+_bp)\s*=\s*Blueprint', content)
    if not bp_names:
        return False
    
    bp_name = bp_names[0]
    
    # 简单字符串替换: @bp.route('/prefix/ -> @bp.route('/
    pattern = f"@{bp_name}.route('/{prefix_to_remove}/"
    replacement = f"@{bp_name}.route('/"
    content = content.replace(pattern, replacement)
    
    # 检查是否有更改
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

print("=" * 80)
print("🔧 修复 Flask 蓝图路由定义")
print("=" * 80)

for filename, prefix in blueprint_mappings.items():
    filepath = os.path.join(routes_dir, filename)
    
    if not os.path.exists(filepath):
        print(f"❌ {filename}: 文件不存在")
        continue
    
    # 修复前，显示原始路由
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        routes_before = re.findall(f"@\\w+_bp\\.route\\('([^']+)'", content)
    
    # 执行修复
    if fix_blueprint_routes(filepath, prefix):
        # 显示修复后的路由
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            routes_after = re.findall(f"@\\w+_bp\\.route\\('([^']+)'", content)
        
        print(f"✅ {filename}: 修复成功")
        print(f"   修复前: {routes_before[:3] if len(routes_before) <= 3 else routes_before[:3] + ['...']}")
        print(f"   修复后: {routes_after[:3] if len(routes_after) <= 3 else routes_after[:3] + ['...']}")
    else:
        print(f"⏭️  {filename}: 无需修改")

print("\n" + "=" * 80)
print("✅ 修复完成！")
print("=" * 80)
print("\n💡 修复说明:")
print("   - 蓝图在 app.py 中用 url_prefix='/api' 注册")
print("   - 蓝图中的路由应该是相对路径 (如 /start)")
print("   - 最终的完整路由会自动添加 /api 前缀 (如 /api/extract/start)")
print("\n📝 修复内容:")
print("   - /extract/start  → /start")
print("   - /dashboard/recent → /recent")
print("   - /knowledge/list → /list")
print("   - 等等...")
print("\n🔄 需要重启后端服务以使用修复后的路由")
