#!/bin/bash
# 字段配置功能测试执行脚本

echo "🚀 开始字段配置功能测试"

# 检查服务状态
echo "1. 检查服务状态..."
if curl -s http://localhost:5001/health > /dev/null; then
    echo "✅ 后端服务正常"
else
    echo "❌ 后端服务未启动"
    exit 1
fi

if curl -s http://localhost:5174 > /dev/null; then
    echo "✅ 前端服务正常"
else
    echo "❌ 前端服务未启动"
    exit 1
fi

# 运行Python测试
echo "2. 运行功能测试..."
python test_field_config_functionality.py

# 检查测试结果
if [ -f "field_config_test_report.json" ]; then
    echo "3. 测试完成，查看详细报告..."
    cat field_config_test_report.json | jq '.summary'
else
    echo "❌ 测试报告未生成"
    exit 1
fi

echo "🎉 测试执行完成！"
