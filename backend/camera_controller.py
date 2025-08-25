"""
摄像头控制器 - 负责摄像头的打开、关闭、录制等操作
"""
import cv2
import numpy as np
from datetime import datetime
import time
import os
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QTimer
from .camera_interface import CameraInterface


class CameraWorker(QThread):
    """摄像头工作线程"""
    frame_ready = pyqtSignal(np.ndarray)
    
    def __init__(self, camera_interface):
        super().__init__()
        self.camera_interface = camera_interface
        self.is_running = False
        self.is_recording = False
        self.video_writer = None
        self.recording_start_time = None
        
    def run(self):
        """线程主函数"""
        self.is_running = True
        while self.is_running:
            frame = self.camera_interface.read_frame()
            if frame is not None:
                # 发送帧信号
                self.frame_ready.emit(frame)
                
                # 如果正在录制，写入视频
                if self.is_recording and self.video_writer is not None:
                    self.video_writer.write(frame)
                    
            self.msleep(30)  # 约33fps
            
    def start_recording(self, filename, fps=30.0):
        """开始录制"""
        frame = self.camera_interface.read_frame()
        if frame is None:
            return False
            
        height, width = frame.shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(filename, fourcc, fps, (width, height))
        self.is_recording = True
        self.recording_start_time = time.time()
        return True
        
    def stop_recording(self):
        """停止录制"""
        self.is_recording = False
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
            
        # 计算录制时长
        duration = 0
        if self.recording_start_time:
            duration = time.time() - self.recording_start_time
            self.recording_start_time = None
            
        return duration
        
    def stop(self):
        """停止线程"""
        self.is_running = False
        if self.is_recording:
            self.stop_recording()
        self.wait()


class CameraController(QObject):
    """摄像头控制器"""
    
    # 信号定义
    frame_ready = pyqtSignal(np.ndarray)
    status_changed = pyqtSignal(str)
    recording_time_updated = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.camera_interface = None
        self.worker = None
        self.is_opened = False
        self.current_filename = None
        self.recording_start_time = None
        
        # 录制计时器
        self.recording_timer = QTimer()
        self.recording_timer.timeout.connect(self.update_recording_time)
        
    def open_camera(self, camera_id=0):
        """打开摄像头"""
        try:
            # 创建摄像头接口（可扩展性设计）
            self.camera_interface = CameraInterface(camera_id)
            if not self.camera_interface.open():
                return False
                
            # 创建并启动工作线程
            self.worker = CameraWorker(self.camera_interface)
            self.worker.frame_ready.connect(self.frame_ready.emit)
            self.worker.start()
            
            self.is_opened = True
            self.status_changed.emit("已连接")
            return True
            
        except Exception as e:
            print(f"打开摄像头失败: {e}")
            return False
            
    def close_camera(self):
        """关闭摄像头"""
        if self.worker:
            self.worker.stop()
            self.worker = None
            
        if self.camera_interface:
            self.camera_interface.close()
            self.camera_interface = None
            
        self.is_opened = False
        self.status_changed.emit("未连接")
        
    def is_camera_opened(self):
        """检查摄像头是否已打开"""
        return self.is_opened
        
    def start_recording(self, filename):
        """开始录制"""
        if not self.worker:
            return False
            
        # 确保目录存在
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        if self.worker.start_recording(filename):
            self.current_filename = filename
            self.recording_start_time = datetime.now()
            self.recording_timer.start(1000)  # 每秒更新一次
            return True
        return False
        
    def stop_recording(self):
        """停止录制"""
        if not self.worker:
            return None
            
        duration = self.worker.stop_recording()
        self.recording_timer.stop()
        
        # 生成元数据
        metadata = {
            'filename': self.current_filename,
            'start_time': self.recording_start_time.isoformat() if self.recording_start_time else None,
            'duration': duration,
            'end_time': datetime.now().isoformat(),
            'camera_info': self.camera_interface.get_camera_info() if self.camera_interface else {},
            'recording_params': {
                'fps': 30.0,
                'codec': 'mp4v',
                'format': 'mp4'
            }
        }
        
        self.current_filename = None
        self.recording_start_time = None
        
        return metadata
        
    def is_recording(self):
        """检查是否正在录制"""
        return self.worker and self.worker.is_recording
        
    def update_recording_time(self):
        """更新录制时间"""
        if self.recording_start_time:
            elapsed = datetime.now() - self.recording_start_time
            hours = int(elapsed.total_seconds() // 3600)
            minutes = int((elapsed.total_seconds() % 3600) // 60)
            seconds = int(elapsed.total_seconds() % 60)
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.recording_time_updated.emit(time_str) 