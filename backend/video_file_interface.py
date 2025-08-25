"""
视频文件接口 - 用于读取和处理本地视频文件
扩展camera_interface.py的基础接口
"""
import cv2
import numpy as np
from .camera_interface import BaseCameraInterface
import os


class VideoFileInterface(BaseCameraInterface):
    """视频文件接口实现"""
    
    def __init__(self, video_path):
        self.video_path = video_path
        self.capture = None
        self.frame_width = 0
        self.frame_height = 0
        self.fps = 0
        self.total_frames = 0
        self.current_frame = 0
        self.is_opened = False
        
    def open(self):
        """打开视频文件"""
        try:
            if not os.path.exists(self.video_path):
                print(f"视频文件不存在: {self.video_path}")
                return False
                
            self.capture = cv2.VideoCapture(self.video_path)
            if not self.capture.isOpened():
                print(f"无法打开视频文件: {self.video_path}")
                return False
            
            # 获取视频属性
            self.frame_width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.frame_height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.fps = self.capture.get(cv2.CAP_PROP_FPS)
            self.total_frames = int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))
            self.current_frame = 0
            self.is_opened = True
            
            print(f"视频文件打开成功: {self.video_path}")
            print(f"分辨率: {self.frame_width}x{self.frame_height}, FPS: {self.fps}, 总帧数: {self.total_frames}")
            
            return True
            
        except Exception as e:
            print(f"打开视频文件失败: {e}")
            return False
    
    def close(self):
        """关闭视频文件"""
        if self.capture:
            self.capture.release()
            self.capture = None
        self.is_opened = False
        self.current_frame = 0
    
    def read_frame(self):
        """读取下一帧"""
        if self.capture and self.capture.isOpened():
            ret, frame = self.capture.read()
            if ret:
                self.current_frame += 1
                return frame
            else:
                # 视频结束，重置到开头
                self.reset_to_beginning()
        return None
    
    def reset_to_beginning(self):
        """重置到视频开头"""
        if self.capture:
            self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.current_frame = 0
    
    def seek_to_frame(self, frame_number):
        """跳转到指定帧"""
        if self.capture and 0 <= frame_number < self.total_frames:
            self.capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            self.current_frame = frame_number
            return True
        return False
    
    def seek_to_time(self, seconds):
        """跳转到指定时间"""
        if self.capture and self.fps > 0:
            frame_number = int(seconds * self.fps)
            return self.seek_to_frame(frame_number)
        return False
    
    def get_current_time(self):
        """获取当前播放时间"""
        if self.fps > 0:
            return self.current_frame / self.fps
        return 0
    
    def get_duration(self):
        """获取视频总时长"""
        if self.fps > 0:
            return self.total_frames / self.fps
        return 0
    
    def get_progress(self):
        """获取播放进度(0-1)"""
        if self.total_frames > 0:
            return self.current_frame / self.total_frames
        return 0
    
    def get_camera_info(self):
        """获取视频文件信息"""
        return {
            'type': 'video_file',
            'video_path': self.video_path,
            'resolution': f"{self.frame_width}x{self.frame_height}",
            'fps': self.fps,
            'total_frames': self.total_frames,
            'duration': self.get_duration(),
            'current_frame': self.current_frame,
            'current_time': self.get_current_time(),
            'progress': self.get_progress()
        }
    
    def is_video_file(self):
        """检查是否为视频文件接口"""
        return True
    
    def has_more_frames(self):
        """检查是否还有更多帧"""
        return self.current_frame < self.total_frames
    
    @staticmethod
    def get_supported_formats():
        """获取支持的视频格式"""
        return [
            '.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', 
            '.webm', '.m4v', '.3gp', '.mpg', '.mpeg'
        ]
    
    @staticmethod
    def is_supported_format(file_path):
        """检查文件格式是否支持"""
        if not file_path:
            return False
        
        ext = os.path.splitext(file_path)[1].lower()
        return ext in VideoFileInterface.get_supported_formats()