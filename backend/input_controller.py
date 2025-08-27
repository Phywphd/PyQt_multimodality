"""
输入控制器 - 统一管理摄像头和视频文件输入源
扩展原有camera_controller.py的功能
"""
import cv2
import numpy as np
from datetime import datetime
import time
import os
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QTimer
from .camera_interface import CameraInterface
from .video_file_interface import VideoFileInterface


class InputWorker(QThread):
    """输入工作线程 - 支持摄像头和视频文件"""
    frame_ready = pyqtSignal(np.ndarray)
    input_info_updated = pyqtSignal(dict)
    
    def __init__(self, input_interface):
        super().__init__()
        self.input_interface = input_interface
        self.is_running = False
        self.is_recording = False
        self.video_writer = None
        self.recording_start_time = None
        self.frame_delay = 30  # 默认延迟30ms
        self.is_paused = False  # 暂停状态
        
    def set_frame_rate(self, fps):
        """设置帧率"""
        if fps > 0:
            self.frame_delay = int(1000 / fps)  # 转换为毫秒延迟
        
    def run(self):
        """线程主函数"""
        self.is_running = True
        while self.is_running:
            # 如果暂停，等待恢复
            if self.is_paused:
                self.msleep(100)  # 暂停时休眠100ms
                continue
                
            frame = self.input_interface.read_frame()
            if frame is not None:
                # 发送帧信号
                self.frame_ready.emit(frame)
                
                # 如果正在录制，写入视频
                if self.is_recording and self.video_writer is not None:
                    self.video_writer.write(frame)
                
                # 发送输入源信息更新
                if hasattr(self.input_interface, 'get_camera_info'):
                    info = self.input_interface.get_camera_info()
                    self.input_info_updated.emit(info)
                    
            # 根据输入类型调整延迟
            if hasattr(self.input_interface, 'is_video_file') and self.input_interface.is_video_file():
                # 视频文件按照其fps播放
                if hasattr(self.input_interface, 'fps') and self.input_interface.fps > 0:
                    delay = int(1000 / self.input_interface.fps)
                    self.msleep(delay)
                else:
                    self.msleep(33)  # 默认30fps
            else:
                # 摄像头使用固定延迟
                self.msleep(self.frame_delay)
            
    def start_recording(self, filename, fps=30.0):
        """开始录制"""
        frame = self.input_interface.read_frame()
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
    
    def pause(self):
        """暂停播放"""
        self.is_paused = True
    
    def resume(self):
        """恢复播放"""
        self.is_paused = False
    
    def toggle_pause(self):
        """切换暂停/播放状态"""
        self.is_paused = not self.is_paused
        return not self.is_paused  # 返回是否正在播放


class InputController(QObject):
    """输入控制器主类 - 统一管理多种输入源"""
    
    # 信号定义
    frame_ready = pyqtSignal(np.ndarray)
    status_changed = pyqtSignal(str)
    recording_time_updated = pyqtSignal(str)
    input_info_updated = pyqtSignal(dict)
    input_type_changed = pyqtSignal(str)  # "camera" 或 "video"
    input_closed = pyqtSignal()  # 输入源关闭信号
    
    def __init__(self):
        super().__init__()
        self.input_interface = None
        self.worker = None
        self.is_opened = False
        self.current_filename = None
        self.recording_start_time = None
        self.input_type = None  # "camera" 或 "video"
        
        # 录制计时器
        self.recording_timer = QTimer()
        self.recording_timer.timeout.connect(self.update_recording_time)
        
    def open_camera(self, camera_id=0):
        """打开摄像头"""
        try:
            # 关闭当前输入
            self.close_input()
            
            # 创建摄像头接口
            self.input_interface = CameraInterface(camera_id)
            if not self.input_interface.open():
                return False
                
            # 创建并启动工作线程
            self.worker = InputWorker(self.input_interface)
            self.worker.frame_ready.connect(self.frame_ready.emit)
            self.worker.input_info_updated.connect(self.input_info_updated.emit)
            self.worker.start()
            
            self.is_opened = True
            self.input_type = "camera"
            self.status_changed.emit("摄像头已连接")
            self.input_type_changed.emit("camera")
            return True
            
        except Exception as e:
            print(f"打开摄像头失败: {e}")
            return False
    
    def open_video_file(self, video_path):
        """打开视频文件"""
        try:
            # 关闭当前输入
            self.close_input()
            
            # 检查文件是否存在和格式是否支持
            if not os.path.exists(video_path):
                self.status_changed.emit("视频文件不存在")
                return False
                
            if not VideoFileInterface.is_supported_format(video_path):
                self.status_changed.emit("不支持的视频格式")
                return False
            
            # 创建视频文件接口
            self.input_interface = VideoFileInterface(video_path)
            if not self.input_interface.open():
                return False
            
            # 创建并启动工作线程
            self.worker = InputWorker(self.input_interface)
            self.worker.frame_ready.connect(self.frame_ready.emit)
            self.worker.input_info_updated.connect(self.input_info_updated.emit)
            self.worker.start()
            
            # 视频文件默认暂停
            self.worker.toggle_pause()  # 设置为暂停状态
            
            # 显示第一帧
            frame = self.input_interface.read_frame()
            if frame is not None:
                self.frame_ready.emit(frame)
                # 重置到第一帧
                self.input_interface.seek_to_frame(0)
            
            self.is_opened = True
            self.input_type = "video"
            self.status_changed.emit(f"视频文件已加载（已暂停）: {os.path.basename(video_path)}")
            self.input_type_changed.emit("video")
            return True
            
        except Exception as e:
            print(f"打开视频文件失败: {e}")
            self.status_changed.emit(f"打开视频失败: {str(e)}")
            return False
            
    def close_input(self):
        """关闭当前输入源"""
        if self.worker:
            self.worker.stop()
            self.worker = None
            
        if self.input_interface:
            self.input_interface.close()
            self.input_interface = None
            
        self.is_opened = False
        self.input_type = None
        self.status_changed.emit("未连接")
        self.input_closed.emit()  # 发送关闭信号
        
    def is_input_opened(self):
        """检查输入源是否已打开"""
        return self.is_opened
        
    def get_input_type(self):
        """获取当前输入类型"""
        return self.input_type
        
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
            'input_type': self.input_type,
            'input_info': self.input_interface.get_camera_info() if self.input_interface else {},
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
    
    def get_current_frame(self):
        """获取当前帧"""
        if self.input_interface:
            return self.input_interface.read_frame()
        return None
    
    def get_input_info(self):
        """获取输入源信息"""
        if self.input_interface and hasattr(self.input_interface, 'get_camera_info'):
            return self.input_interface.get_camera_info()
        return {}
    
    # 视频文件特有的控制方法
    def seek_to_time(self, seconds):
        """跳转到指定时间 (仅视频文件)"""
        if self.input_type == "video" and hasattr(self.input_interface, 'seek_to_time'):
            return self.input_interface.seek_to_time(seconds)
        return False
    
    def reset_video(self):
        """重置视频到开头 (仅视频文件)"""
        if self.input_type == "video" and hasattr(self.input_interface, 'reset_to_beginning'):
            self.input_interface.reset_to_beginning()
            return True
        return False
    
    def toggle_play_pause(self):
        """切换播放/暂停状态"""
        if self.worker:
            return self.worker.toggle_pause()
        return False
    
    def pause_playback(self):
        """暂停播放"""
        if self.worker:
            self.worker.pause()
    
    def resume_playback(self):
        """恢复播放"""
        if self.worker:
            self.worker.resume()
    
    def seek_to_progress(self, progress):
        """跳转到指定进度 (0.0-1.0)"""
        if self.input_type == "video" and hasattr(self.input_interface, 'seek_to_progress'):
            return self.input_interface.seek_to_progress(progress)
        return False
    
    def get_video_progress(self):
        """获取视频播放进度 (仅视频文件)"""
        if self.input_type == "video" and hasattr(self.input_interface, 'get_progress'):
            return self.input_interface.get_progress()
        return 0.0