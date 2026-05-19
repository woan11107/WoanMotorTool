#!/bin/bash
# 电机工具打包脚本 - Linux/macOS
# 生成单一二进制 motor_tool(自动识别 CANable / Damiao,可用 --type 强制指定)

echo "================================"
echo "  电机工具打包脚本"
echo "================================"

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3，请先安装 Python"
    exit 1
fi

echo "Python 版本:"
python3 --version

# 检查并安装依赖
echo ""
echo "正在安装依赖..."
pip3 install -r requirements.txt

# 安装 PyInstaller
echo ""
echo "正在安装 PyInstaller..."
pip3 install pyinstaller

# --------------------------------------------------
# 打包 motor_tool
# --------------------------------------------------
echo ""
echo ">>> 开始打包 motor_tool ..."
pyinstaller --onefile \
    --name motor_tool \
    --console \
    --clean \
    --paths src \
    src/motor_tool.py

if [ $? -ne 0 ]; then
    echo "motor_tool 打包失败，请检查错误信息"
    exit 1
fi

# --------------------------------------------------
# 汇总结果
# --------------------------------------------------
echo ""
echo "================================"
echo "  打包成功！"
echo "================================"
echo "可执行文件位置:"
echo "  ./dist/motor_tool"
echo ""
echo "使用方法:"
echo "  ./dist/motor_tool                  # 自动识别 CANable / Damiao"
echo "  ./dist/motor_tool --type canable   # 强制按 CANable 协议"
echo "  ./dist/motor_tool --type damiao    # 强制按 Damiao 协议"
