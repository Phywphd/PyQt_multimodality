#!/bin/bash

# TTS语音依赖安装脚本
# 用于安装eSpeak语音引擎和中文语音包

echo "=== VLM多模态系统 - TTS语音依赖安装 ==="

# 检查是否为root用户
if [[ $EUID -eq 0 ]]; then
   echo "请不要使用root用户运行此脚本"
   exit 1
fi

# 更新包管理器
echo "正在更新包管理器..."
sudo apt update

# 安装基础eSpeak引擎
echo "正在安装eSpeak语音引擎..."
sudo apt install -y espeak espeak-data libespeak-dev

# 安装eSpeak-NG（更好的语音质量）
echo "正在安装eSpeak-NG..."
sudo apt install -y espeak-ng espeak-ng-data

# 尝试安装中文语音包
echo "正在安装中文语音包..."
sudo apt install -y espeak-ng-espeak espeak-ng-voice-mandarin 2>/dev/null || echo "中文语音包可能不可用，将使用默认语音"

# 安装其他可能的中文语音支持
sudo apt install -y festival festival-dev festvox-mandarin 2>/dev/null || echo "Festival中文语音包安装可选"

# 测试语音功能
echo "正在测试语音功能..."
if command -v espeak >/dev/null 2>&1; then
    echo "eSpeak安装成功！正在测试..."
    echo "你应该会听到语音：'Hello, this is a test'"
    espeak "Hello, this is a test" 2>/dev/null
    
    # 测试中文语音
    echo "正在测试中文语音..."
    espeak -v zh "你好，这是中文语音测试" 2>/dev/null || espeak -v mandarin "你好，这是中文语音测试" 2>/dev/null || espeak "ni hao, zhe shi zhong wen yu yin ce shi" 2>/dev/null
    
    echo "如果你听到了语音，说明安装成功！"
else
    echo "eSpeak安装失败，请手动检查"
    exit 1
fi

# 显示可用语音
echo ""
echo "可用的语音列表："
espeak --voices 2>/dev/null | head -20

echo ""
echo "=== 安装完成 ==="
echo "提示："
echo "1. 如果WSL2中没有声音，请确保Windows音频服务正常"
echo "2. 可能需要重启终端或重新加载环境"
echo "3. 如果仍然有问题，请检查PulseAudio配置"

# 检查音频系统
if command -v pactl >/dev/null 2>&1; then
    echo ""
    echo "检查PulseAudio状态："
    pactl info 2>/dev/null | head -5 || echo "PulseAudio可能未运行"
fi

echo ""
echo "现在可以运行VLM系统测试语音功能了！"