#!/bin/bash
# 电机工具打包脚本 - Linux/macOS
# 生成两个版本: motor_tool_canable 和 motor_tool_damiao

echo "================================"
echo "  电机工具打包脚本 (双版本)"
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

BUILD_FAILED=0

# --------------------------------------------------
# 打包 CANable 版本
# --------------------------------------------------
echo ""
echo ">>> [1/2] 开始打包 motor_tool_canable ..."
pyinstaller --onefile \
    --name motor_tool_canable \
    --console \
    --clean \
    --paths src \
    src/motor_tool_canable.py

if [ $? -ne 0 ]; then
    echo "motor_tool_canable 打包失败，请检查错误信息"
    BUILD_FAILED=1
fi

# --------------------------------------------------
# 打包 Damiao 版本
# --------------------------------------------------
echo ""
echo ">>> [2/2] 开始打包 motor_tool_damiao ..."
pyinstaller --onefile \
    --name motor_tool_damiao \
    --console \
    --clean \
    --paths src \
    src/motor_tool_damiao.py

if [ $? -ne 0 ]; then
    echo "motor_tool_damiao 打包失败，请检查错误信息"
    BUILD_FAILED=1
fi

# --------------------------------------------------
# 汇总结果
# --------------------------------------------------
echo ""
if [ $BUILD_FAILED -eq 0 ]; then
    echo "================================"
    echo "  打包成功！"
    echo "================================"
    echo "可执行文件位置:"
    echo "  CANable 版: ./dist/motor_tool_canable"
    echo "  Damiao  版: ./dist/motor_tool_damiao"
    echo ""
    echo "使用方法:"
    echo "  ./dist/motor_tool_canable   # 适用于 CANable / candleLight"
    echo "  ./dist/motor_tool_damiao    # 适用于达妙直连串口"
else
    echo "部分版本打包失败，请检查以上错误信息"
    exit 1
fi
