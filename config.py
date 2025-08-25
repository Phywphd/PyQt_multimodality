"""
应用配置文件
"""
import os

# 应用基本配置
APP_NAME = "摄像头录制系统"
VERSION = "1.0.0"

# 路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
VIDEO_DIR = os.path.join(DATA_DIR, 'videos')
METADATA_DIR = os.path.join(DATA_DIR, 'metadata')
RAW_FRAMES_DIR = os.path.join(DATA_DIR, 'raw_frames')

# 摄像头配置
DEFAULT_CAMERA_ID = 0  # 默认使用第一个摄像头
DEFAULT_RESOLUTION = (1280, 720)  # 默认分辨率
DEFAULT_FPS = 30  # 默认帧率

# 录制配置
VIDEO_CODEC = 'mp4v'  # 视频编码器
VIDEO_FORMAT = '.mp4'  # 视频格式
RECORDING_PREFIX = 'recording'  # 录制文件名前缀

# 界面配置
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
PREVIEW_WIDTH = 640
PREVIEW_HEIGHT = 480

# 数据存储配置
SAVE_RAW_FRAMES = False  # 是否保存原始帧数据
FRAME_SAMPLING_RATE = 30  # 帧采样率（如果保存原始帧）

# 外部设备配置（预留）
EXTERNAL_DEVICE_CONFIG = {
    'type': 'network_camera',  # 设备类型
    'host': '192.168.1.100',   # 设备地址
    'port': 8080,              # 端口
    'protocol': 'rtsp',        # 通信协议
    'auth': {                  # 认证信息
        'username': '',
        'password': ''
    }
} 