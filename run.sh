#!/bin/bash
# VLM多模态演示系统启动脚本（支持中文输入）

# 设置语言环境
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8
export LC_CTYPE=zh_CN.UTF-8

# 设置显示服务器
export DISPLAY=${DISPLAY:-:0}

# 设置输入法环境变量 - 使用ibus
export QT_IM_MODULE=ibus
export GTK_IM_MODULE=ibus
export XMODIFIERS=@im=ibus
export XDG_SESSION_TYPE=x11

# 确保ibus在后台运行
if ! pgrep -x "ibus-daemon" > /dev/null; then
    echo "启动ibus输入法..."
    ibus-daemon -drx &
    sleep 2
else
    echo "ibus输入法已在运行"
fi

# 设置Qt插件路径
export QT_QPA_PLATFORM_PLUGIN_PATH=/home/hyp/miniconda3/envs/qwen_vlm/lib/python3.9/site-packages/PyQt5/Qt5/plugins/platforms

echo "====================================="
echo "VLM多模态演示系统"
echo "====================================="
echo "语言环境: $LANG"
echo "输入法: ibus (使用 Ctrl+Space 切换中文)"
echo "====================================="

# 激活conda环境并运行程序
source ~/miniconda3/etc/profile.d/conda.sh
conda activate qwen_vlm

# 运行主程序
python vlm_main.py

echo "程序结束"