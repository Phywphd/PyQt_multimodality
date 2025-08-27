#!/bin/bash

# WSL2音频修复脚本 - 解决aplay not found问题

echo "=== WSL2音频系统修复 ==="

# 检查当前音频状态
echo "检查当前音频工具..."
which aplay || echo "aplay未安装"
which paplay || echo "paplay未安装" 
which pulseaudio || echo "pulseaudio未安装"

echo ""
echo "正在安装音频工具..."

# 安装ALSA工具
sudo apt install -y alsa-utils

# 安装PulseAudio工具
sudo apt install -y pulseaudio pulseaudio-utils

# 启动PulseAudio
echo "启动PulseAudio..."
pulseaudio --start --verbose 2>/dev/null || echo "PulseAudio可能已经在运行"

# 测试音频
echo ""
echo "测试音频输出..."
if which aplay >/dev/null 2>&1; then
    echo "aplay已安装"
else
    echo "aplay安装失败"
fi

if which paplay >/dev/null 2>&1; then
    echo "paplay已安装" 
else
    echo "paplay安装失败"
fi

# 检查音频设备
echo ""
echo "检查音频设备："
pactl list short sinks 2>/dev/null || echo "无法列出音频设备"

# 测试eSpeak
echo ""
echo "测试eSpeak语音..."
espeak "Audio test completed" 2>/dev/null && echo "eSpeak测试成功" || echo "eSpeak测试失败"

echo ""
echo "=== 修复完成 ==="
echo "请重新运行应用测试语音功能"