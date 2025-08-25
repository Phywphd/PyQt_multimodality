# VLM多模态演示系统

基于PyQt5开发的多模态演示应用，集成摄像头录制、视频文件处理、Qwen2.5-VL视觉语言模型分析和语音输出功能。

## 🆕 新功能特性

### 多模态输入支持
- **摄像头输入**：支持实时摄像头视频流
- **视频文件输入**：支持多种格式视频文件（MP4、AVI、MOV等）
- **输入源切换**：可随时在摄像头和视频文件间切换

### VLM智能分析
- **实时画面分析**：基于Qwen2.5-VL模型分析当前画面内容
- **完整视频分析**：对整个视频文件进行深度理解和总结
- **自定义提示词**：支持用户自定义分析角度和要求

### 语音输出
- **文本转语音**：将VLM分析结果转换为语音播报
- **语音控制**：支持开始/停止语音播报
- **多语言支持**：支持中文语音合成

## 项目架构

```
PyQt_multimodality/
├── main.py                     # 原始演示程序入口
├── vlm_main.py                 # VLM版本程序入口 🆕
├── config.py                   # 配置文件
├── requirements.txt            # 项目依赖（已更新）
├── README.md                   # 项目说明（已更新）
│
├── frontend/                   # 前端界面模块
│   ├── main_window.py          # 原始主窗口
│   ├── vlm_main_window.py      # VLM版本主窗口 🆕
│   └── camera_widget.py        # 摄像头显示组件
│
├── backend/                    # 后端业务逻辑模块
│   ├── camera_controller.py    # 原始摄像头控制器
│   ├── input_controller.py     # 统一输入控制器 🆕
│   ├── camera_interface.py     # 摄像头接口抽象层
│   ├── video_file_interface.py # 视频文件接口 🆕
│   ├── vlm_processor.py        # VLM处理器 🆕
│   ├── tts_processor.py        # 语音合成处理器 🆕
│   └── data_manager.py         # 数据管理器
│
└── data/                       # 数据存储目录
    ├── videos/                 # 视频文件
    ├── metadata/               # 元数据文件
    └── index.json             # 录制索引
```

## 环境配置

### 1. 创建Conda环境
```bash
conda create -n qwen_vlm python=3.9 -y
conda activate qwen_vlm
```

### 2. 安装核心依赖
```bash
# Transformers和加速器
pip install transformers==4.51.3 accelerate

# Qwen VL工具包（推荐decord后端）
pip install qwen-vl-utils[decord]

# 其他依赖
pip install -r requirements.txt
```

### 3. 安装PyTorch
```bash
# CUDA版本（推荐）
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# CPU版本
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

## 使用方法

### 启动VLM演示系统
```bash
cd PyQt_multimodality
python vlm_main.py
```

### 启动原始录制系统
```bash
python main.py
```

## 功能使用指南

### 1. 输入源设置
- 点击"打开摄像头"连接本地摄像头
- 点击"打开视频文件"加载本地视频文件
- 支持的视频格式：`.mp4`, `.avi`, `.mov`, `.mkv`, `.flv`, `.wmv`, `.webm`, `.m4v`

### 2. VLM分析功能
- **分析当前画面**：对摄像头实时画面或视频当前帧进行分析
- **分析整个视频**：对完整视频文件进行深度理解（仅视频文件输入时可用）
- **自定义提示词**：在提示词输入框中输入分析要求

### 3. 语音输出
- VLM分析完成后，点击"朗读分析结果"进行语音播报
- 支持中途停止朗读功能

### 4. 视频控制（仅视频文件）
- 进度条显示视频播放进度
- "重置"按钮可将视频重置到开头

## 技术特性

### VLM集成
- 基于**Qwen2.5-VL**官方API进行视觉语言理解
- 支持图像和视频的多模态分析
- 采用官方推荐的模型加载和推理配置

### 多线程架构
- **输入线程**：独立处理摄像头/视频文件读取
- **VLM处理线程**：后台执行模型推理，不阻塞UI
- **语音合成线程**：异步进行文本转语音

### 数据管理
- 保持原有的录制和元数据管理功能
- 扩展元数据包含输入源类型信息
- 支持录制历史查看和管理

## 系统要求

### 硬件要求
- **推荐配置**：NVIDIA GPU (8GB+ VRAM) 用于VLM模型推理
- **最低配置**：支持CPU推理（速度较慢）
- **摄像头**：USB摄像头或内置摄像头
- **音频输出**：扬声器或耳机

### 软件要求
- Python 3.9+
- PyQt5 5.15+
- CUDA 11.8+（GPU加速，可选）

## 模型说明

项目默认使用 `Qwen/Qwen2.5-VL-3B-Instruct` 模型，首次运行时会自动下载。

### 支持的模型
- `Qwen/Qwen2.5-VL-3B-Instruct`（推荐，平衡性能和速度）
- `Qwen/Qwen2.5-VL-7B-Instruct`（更高精度，需要更多资源）
- `Qwen/Qwen2.5-VL-72B-Instruct`（最高精度，需要多GPU）

可在 `backend/vlm_processor.py` 中修改模型路径。

## 故障排除

### 常见问题
1. **模型下载缓慢**：使用国内镜像或本地模型路径
2. **内存不足**：降低模型尺寸或使用CPU推理
3. **摄像头无法打开**：检查设备权限和驱动
4. **语音无输出**：检查系统音频设置

### 日志调试
程序运行时会在终端显示详细日志，包括：
- 模型加载进度
- VLM推理状态
- 输入源连接状态

## 开发说明

### 扩展VLM功能
可在 `vlm_processor.py` 中扩展更多VLM处理功能：
- 添加新的提示词模板
- 实现批量视频处理
- 集成其他视觉语言模型

### 自定义输入源
通过继承 `BaseCameraInterface` 可添加新的输入源：
- 网络摄像头(RTSP)
- 图像序列
- 屏幕录制

## 参考资源

- [Qwen2.5-VL官方仓库](https://github.com/QwenLM/Qwen2.5-VL)
- [Qwen2.5-VL视频理解示例](/home/hyp/research/multimodal_demo/Qwen2.5-VL/cookbooks/video_understanding.ipynb)
- [PyQt5官方文档](https://doc.qt.io/qtforpython-5/)

## 许可证

本项目遵循原有许可证协议。

---

**作者**: Haoyu Pan (haoyupan@umich.edu)
**更新时间**: 2025年8月