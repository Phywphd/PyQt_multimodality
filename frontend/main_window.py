"""
主窗口界面
"""
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel,
                             QGroupBox, QTextEdit, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QImage

from .camera_widget import CameraWidget
from backend.camera_controller import CameraController
from backend.data_manager import DataManager


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.camera_controller = CameraController()
        self.data_manager = DataManager()
        self.init_ui()
        self.connect_signals()
        
    def init_ui(self):
        """初始化UI界面"""
        self.setWindowTitle("视频数据记录系统demo")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中心widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 左侧：摄像头显示区域
        left_layout = QVBoxLayout()
        
        # 摄像头widget
        self.camera_widget = CameraWidget()
        left_layout.addWidget(self.camera_widget)
        
        # 控制按钮组
        control_group = QGroupBox("控制面板")
        control_layout = QHBoxLayout()
        
        self.btn_open_camera = QPushButton("打开摄像头")
        self.btn_open_camera.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {#鼠标触碰变色
                background-color: #45a049;
            }
        """)
        
        self.btn_start_record = QPushButton("开始录制")
        self.btn_start_record.setEnabled(False)
        self.btn_start_record.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        
        self.btn_stop_record = QPushButton("停止录制")
        self.btn_stop_record.setEnabled(False)
        self.btn_stop_record.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        
        control_layout.addWidget(self.btn_open_camera)
        control_layout.addWidget(self.btn_start_record)
        control_layout.addWidget(self.btn_stop_record)
        control_group.setLayout(control_layout)
        
        left_layout.addWidget(control_group)
        
        # 右侧：信息显示区域
        right_layout = QVBoxLayout()
        
        # 状态信息
        status_group = QGroupBox("状态信息")
        status_layout = QVBoxLayout()
        
        self.lbl_camera_status = QLabel("摄像头状态：未连接")
        self.lbl_camera_status.setFont(QFont("Arial", 12))
        
        self.lbl_recording_status = QLabel("录制状态：未开始")
        self.lbl_recording_status.setFont(QFont("Arial", 12))
        
        self.lbl_recording_time = QLabel("录制时长：00:00:00")
        self.lbl_recording_time.setFont(QFont("Arial", 12))
        
        status_layout.addWidget(self.lbl_camera_status)
        status_layout.addWidget(self.lbl_recording_status)
        status_layout.addWidget(self.lbl_recording_time)
        status_group.setLayout(status_layout)
        
        # 录制历史
        history_group = QGroupBox("录制历史")
        history_layout = QVBoxLayout()
        
        self.text_history = QTextEdit()
        self.text_history.setReadOnly(True)
        history_layout.addWidget(self.text_history)
        history_group.setLayout(history_layout)
        
        right_layout.addWidget(status_group)
        right_layout.addWidget(history_group)
        
        # 添加到主布局
        main_layout.addLayout(left_layout, 3)  # 左侧占3份
        main_layout.addLayout(right_layout, 1)  # 右侧占1份
        
    def connect_signals(self):
        """连接信号槽"""
        # 按钮点击事件
        self.btn_open_camera.clicked.connect(self.on_open_camera)
        self.btn_start_record.clicked.connect(self.on_start_record)
        self.btn_stop_record.clicked.connect(self.on_stop_record)
        
        # 后端信号
        self.camera_controller.frame_ready.connect(self.camera_widget.update_frame)
        self.camera_controller.status_changed.connect(self.on_camera_status_changed)
        self.camera_controller.recording_time_updated.connect(self.on_recording_time_updated)
        
    def on_open_camera(self):
        """打开摄像头"""
        if self.camera_controller.is_camera_opened():
            # 关闭摄像头
            self.camera_controller.close_camera()
            self.btn_open_camera.setText("打开摄像头")
            self.btn_start_record.setEnabled(False)
            self.lbl_camera_status.setText("摄像头状态：未连接")
        else:
            # 打开摄像头
            if self.camera_controller.open_camera():
                self.btn_open_camera.setText("关闭摄像头")
                self.btn_start_record.setEnabled(True)
                self.lbl_camera_status.setText("摄像头状态：已连接")
            else:
                QMessageBox.critical(self, "错误", "无法打开摄像头！")
                
    def on_start_record(self):
        """开始录制"""
        filename = self.data_manager.generate_filename()
        if self.camera_controller.start_recording(filename):
            self.btn_start_record.setEnabled(False)
            self.btn_stop_record.setEnabled(True)
            self.lbl_recording_status.setText("录制状态：正在录制")
            
    def on_stop_record(self):
        """停止录制"""
        metadata = self.camera_controller.stop_recording()
        if metadata:
            self.btn_start_record.setEnabled(True)
            self.btn_stop_record.setEnabled(False)
            self.lbl_recording_status.setText("录制状态：已停止")
            self.lbl_recording_time.setText("录制时长：00:00:00")
            
            # 保存元数据
            self.data_manager.save_metadata(metadata)
            
            # 更新历史记录
            self.update_history()
            
    def on_camera_status_changed(self, status):
        """摄像头状态改变"""
        self.lbl_camera_status.setText(f"摄像头状态：{status}")
        
    def on_recording_time_updated(self, time_str):
        """更新录制时间"""
        self.lbl_recording_time.setText(f"录制时长：{time_str}")
        
    def update_history(self):
        """更新录制历史"""
        history = self.data_manager.get_recording_history()
        history_text = ""
        for record in history[-10:]:  # 显示最近10条
            history_text += f"文件：{record['filename']}\n"
            history_text += f"时间：{record['timestamp']}\n"
            history_text += f"时长：{record['duration']}秒\n"
            history_text += "-" * 40 + "\n"
        self.text_history.setText(history_text)
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.camera_controller.is_recording():
            reply = QMessageBox.question(self, '确认', '正在录制中，确定要退出吗？',
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                event.ignore()
                return
                
        self.camera_controller.close_camera()
        event.accept() 