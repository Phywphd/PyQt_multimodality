"""
摄像头接口抽象层 - 提供统一的摄像头访问接口
便于后续扩展支持不同类型的摄像头设备
"""
import cv2
import numpy as np
from abc import ABC, abstractmethod


class BaseCameraInterface(ABC):
    """摄像头接口基类"""
    
    @abstractmethod
    def open(self):
        """打开摄像头"""
        pass
        
    @abstractmethod
    def close(self):
        """关闭摄像头"""
        pass
        
    @abstractmethod
    def read_frame(self):
        """读取一帧图像"""
        pass
        
    @abstractmethod
    def get_camera_info(self):
        """获取摄像头信息"""
        pass


class CameraInterface(BaseCameraInterface):
    """
    默认摄像头接口实现 - 使用OpenCV访问本地摄像头
    后续可以创建其他实现类来支持不同的设备
    """
    
    def __init__(self, camera_id=0):
        self.camera_id = camera_id
        self.capture = None
        self.frame_width = 0
        self.frame_height = 0
        self.fps = 0
        
    def open(self):
        """打开摄像头"""
        try:
            self.capture = cv2.VideoCapture(self.camera_id)
            if not self.capture.isOpened():
                return False
                
            # 设置摄像头参数
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.capture.set(cv2.CAP_PROP_FPS, 30)
            
            # 获取实际参数
            self.frame_width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.frame_height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.fps = int(self.capture.get(cv2.CAP_PROP_FPS))
            
            return True
            
        except Exception as e:
            print(f"打开摄像头失败: {e}")
            return False
            
    def close(self):
        """关闭摄像头"""
        if self.capture:
            self.capture.release()
            self.capture = None
            
    def read_frame(self):
        """读取一帧图像"""
        if self.capture and self.capture.isOpened():
            ret, frame = self.capture.read()
            if ret:
                return frame
        return None
        
    def get_camera_info(self):
        """获取摄像头信息"""
        return {
            'type': 'local_camera',
            'camera_id': self.camera_id,
            'resolution': f"{self.frame_width}x{self.frame_height}",
            'fps': self.fps,
            'backend': cv2.CAP_PROP_BACKEND if hasattr(cv2, 'CAP_PROP_BACKEND') else 'unknown'
        }


class ExternalCameraInterface(BaseCameraInterface):
    """
    外部设备摄像头接口示例
    这是一个模板，展示如何扩展支持外部设备
    """
    
    def __init__(self, device_config):
        """
        初始化外部设备
        device_config: 设备配置信息，如IP地址、端口、认证信息等
        """
        self.device_config = device_config
        self.is_connected = False
        
    def open(self):
        """连接到外部设备"""
        # TODO: 实现具体的设备连接逻辑
        # 例如：通过网络协议连接到设备
        # self.device = connect_to_device(self.device_config)
        pass
        
    def close(self):
        """断开设备连接"""
        # TODO: 实现断开连接逻辑
        pass
        
    def read_frame(self):
        """从设备读取帧数据"""
        # TODO: 实现从设备读取数据的逻辑
        # 可能需要解码特定的数据格式
        pass
        
    def get_camera_info(self):
        """获取设备信息"""
        return {
            'type': 'external_device',
            'config': self.device_config
        } 