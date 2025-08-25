# 摄像头录制系统

基于PyQt5开发的摄像头录制应用，支持视频录制和元数据管理，具有良好的可扩展性。

## 项目结构

```
pyqt/
├── main.py              # 主程序入口
├── config.py            # 配置文件
├── requirements.txt     # 项目依赖
├── README.md           # 项目说明
│
├── frontend/           # 前端界面模块
│   ├── __init__.py
│   ├── main_window.py  # 主窗口
│   └── camera_widget.py # 摄像头显示组件
│
├── backend/            # 后端业务逻辑模块
│   ├── __init__.py
│   ├── camera_controller.py  # 摄像头控制器
│   ├── camera_interface.py   # 摄像头接口抽象层
│   └── data_manager.py       # 数据管理器
│
└── data/              # 数据存储目录（运行时自动创建）
    ├── videos/        # 视频文件
    ├── metadata/      # 元数据文件
    ├── raw_frames/    # 原始帧数据（可选）
    └── index.json     # 录制索引
```

## 核心架构设计

### 1. 前后端分离架构

- **前端（frontend）**：负责UI界面显示和用户交互
  - `MainWindow`: 主窗口，包含所有UI组件和布局
  - `CameraWidget`: 专门负责视频画面显示的组件

- **后端（backend）**：负责业务逻辑和数据处理
  - `CameraController`: 摄像头控制核心，管理摄像头状态和录制流程
  - `CameraInterface`: 摄像头接口抽象层，便于扩展不同设备
  - `DataManager`: 数据管理器，负责文件存储和元数据管理

### 2. 信号槽机制

PyQt使用信号槽机制实现组件间通信：

```python
# 后端发送信号
self.camera_controller.frame_ready.connect(self.camera_widget.update_frame)

# 前端响应用户操作
self.btn_open_camera.clicked.connect(self.on_open_camera)
```

### 3. 多线程设计

使用`QThread`将摄像头读取操作放在独立线程中，避免阻塞UI：

```python
class CameraWorker(QThread):
    frame_ready = pyqtSignal(np.ndarray)
    
    def run(self):
        # 在独立线程中读取摄像头数据
        while self.is_running:
            frame = self.camera_interface.read_frame()
            self.frame_ready.emit(frame)
```

## 数据存储设计

### 1. 视频文件
- 格式：MP4
- 编码：mp4v
- 命名：`recording_YYYYMMDD_HHMMSS.mp4`

### 2. 元数据存储

支持多种格式，满足不同训练需求：

- **JSON格式**：人类可读，便于调试
- **Pickle格式**：保持Python对象完整性
- **索引文件**：快速查询所有录制记录

元数据包含内容：
```json
{
    "filename": "视频文件路径",
    "start_time": "开始时间",
    "duration": "时长（秒）",
    "end_time": "结束时间",
    "camera_info": {
        "type": "摄像头类型",
        "resolution": "分辨率",
        "fps": "帧率"
    },
    "recording_params": {
        "fps": 30.0,
        "codec": "mp4v",
        "format": "mp4"
    }
}
```

### 3. 原始帧数据（可选）
- 格式：NumPy数组（.npy）
- 用途：需要逐帧处理的训练场景

## 可扩展性设计

### 1. 摄像头接口抽象

通过`BaseCameraInterface`基类定义统一接口：

```python
class BaseCameraInterface(ABC):
    @abstractmethod
    def open(self):
        pass
    
    @abstractmethod
    def read_frame(self):
        pass
```

### 2. 扩展外部设备

创建新的接口实现类即可支持不同设备：

```python
class ExternalCameraInterface(BaseCameraInterface):
    def __init__(self, device_config):
        # 根据设备配置初始化
        pass
```

### 3. 数据导出接口

`DataManager`提供灵活的数据导出功能：

```python
def export_for_training(self, output_path, format='json'):
    # 支持多种导出格式
    pass
```

## 使用说明

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行程序

```bash
python main.py
```

### 3. 操作流程

1. 点击"打开摄像头"按钮
2. 点击"开始录制"开始录制视频
3. 点击"停止录制"结束录制
4. 查看右侧的录制历史

### 4. 配置修改

编辑`config.py`文件可以修改默认配置。

## 后续扩展建议

1. **支持更多视频格式**：可以添加H.264等编码器
2. **实时处理**：在录制时添加实时图像处理功能
3. **批量导出**：支持批量导出特定格式的训练数据
4. **网络摄像头**：实现RTSP等网络协议支持
5. **数据标注**：添加视频标注功能

## 注意事项

1. 确保电脑有可用的摄像头设备
2. 首次运行会自动创建data目录结构
3. 录制的视频文件可能较大，注意磁盘空间 