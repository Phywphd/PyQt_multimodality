"""
摄像头显示组件
"""
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QImage
import numpy as np


class CameraWidget(QWidget):
    """摄像头显示widget"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 视频显示标签
        self.video_label = QLabel()
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setScaledContents(True)
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: #000000;
                border: 2px solid #333333;
                border-radius: 5px;
            }
        """)
        
        # 显示默认提示
        self.video_label.setText("摄像头未开启")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: #000000;
                color: #ffffff;
                font-size: 20px;
                border: 2px solid #333333;
                border-radius: 5px;
            }
        """)
        
        layout.addWidget(self.video_label)
        self.setLayout(layout)
        
    def update_frame(self, frame):
        """更新显示帧"""
        if frame is None:
            return
            
        # 转换格式
        if len(frame.shape) == 2:  # 灰度图
            height, width = frame.shape
            bytes_per_line = width
            q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
        else:  # 彩色图
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            # OpenCV使用BGR，需要转换为RGB
            frame_rgb = frame[..., ::-1].copy()
            q_image = QImage(frame_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
            
        # 缩放到合适大小
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.video_label.setPixmap(scaled_pixmap)
        
    def clear_display(self):
        """清空显示"""
        self.video_label.clear()
        self.video_label.setText("摄像头未开启")
        self.video_label.setAlignment(Qt.AlignCenter) 