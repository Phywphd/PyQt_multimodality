"""
VLM多模态主窗口界面 - 集成摄像头、视频文件、VLM处理和语音输出
"""
# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QGroupBox, QTextEdit, 
                             QMessageBox, QFileDialog, QSlider, QComboBox,
                             QProgressBar, QSplitter, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap, QImage, QTextCursor

from .camera_widget import CameraWidget
from .chinese_input_widget import ChineseInputLineEdit
from backend.input_controller import InputController
from backend.data_manager import DataManager
from backend.vlm_processor import VLMProcessor
from backend.vlm_remote_processor import VLMRemoteProcessor
from backend.tts_processor import TTSProcessor
from datetime import datetime
import os


class VLMMainWindow(QMainWindow):
    """VLM多模态主窗口类"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化各个处理器
        self.input_controller = InputController()
        self.data_manager = DataManager()
        # VLM处理器 - 支持本地和远程模式
        self.use_remote_vlm = True  # 默认使用远程模式
        self.vlm_processor = VLMRemoteProcessor("10.180.235.247", 8888) if self.use_remote_vlm else VLMProcessor()
        self.tts_processor = TTSProcessor()
        
        # 状态变量
        self.is_vlm_processing = False
        self.current_video_path = None
        
        self.init_ui()
        self.setup_chinese_input()  # 设置中文输入支持
        self.connect_signals()
        
        # 启动模型加载
        QTimer.singleShot(1000, self.load_vlm_model)
    
    def setup_chinese_input(self):
        """设置中文输入支持"""
        try:
            from PyQt5.QtCore import Qt
            # 在窗口级别设置输入法支持
            self.setAttribute(Qt.WA_InputMethodEnabled, True)
            
            # 确保窗口能接收输入法事件
            self.setInputMethodHints(Qt.ImhNone)
            
            # 设置窗口属性支持IME
            self.setAttribute(Qt.WA_KeyCompression, False)
            
        except Exception as e:
            print(f"设置中文输入支持时出错: {e}")
    
    def init_ui(self):
        """初始化UI界面"""
        self.setWindowTitle("VLM多模态演示系统")
        self.setGeometry(100, 100, 1400, 900)
        
        # 创建中心widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局 - 使用分割器
        main_splitter = QSplitter(Qt.Horizontal)
        central_widget.setLayout(QHBoxLayout())
        central_widget.layout().addWidget(main_splitter)
        
        # 左侧面板
        left_panel = self.create_left_panel()
        main_splitter.addWidget(left_panel)
        
        # 右侧面板
        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)
        
        # 设置分割比例
        main_splitter.setStretchFactor(0, 2)  # 左侧占2份
        main_splitter.setStretchFactor(1, 1)  # 右侧占1份
        
    def create_left_panel(self):
        """创建左侧面板"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 视频显示区域
        self.camera_widget = CameraWidget()
        left_layout.addWidget(self.camera_widget)
        
        # 输入源控制组
        input_group = self.create_input_control_group()
        left_layout.addWidget(input_group)
        
        # VLM处理控制组
        vlm_group = self.create_vlm_control_group()
        left_layout.addWidget(vlm_group)
        
        return left_widget
        
    def create_right_panel(self):
        """创建右侧面板"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 状态信息组
        status_group = self.create_status_group()
        right_layout.addWidget(status_group)
        
        # VLM输出显示组
        output_group = self.create_output_group()
        right_layout.addWidget(output_group)
        
        # 语音控制组
        tts_group = self.create_tts_control_group()
        right_layout.addWidget(tts_group)
        
        # 历史记录组
        history_group = self.create_history_group()
        right_layout.addWidget(history_group)
        
        return right_widget
        
    def create_input_control_group(self):
        """创建输入源控制组"""
        group = QGroupBox("输入源控制")
        layout = QVBoxLayout()
        
        # 输入源类型选择
        input_type_layout = QHBoxLayout()
        self.btn_open_camera = QPushButton("打开摄像头")
        self.btn_open_camera.setStyleSheet(self.get_button_style("#4CAF50"))
        
        self.btn_open_video = QPushButton("打开视频文件")
        self.btn_open_video.setStyleSheet(self.get_button_style("#2196F3"))
        
        input_type_layout.addWidget(self.btn_open_camera)
        input_type_layout.addWidget(self.btn_open_video)
        layout.addLayout(input_type_layout)
        
        # 录制控制
        record_layout = QHBoxLayout()
        self.btn_start_record = QPushButton("开始录制")
        self.btn_start_record.setEnabled(False)
        self.btn_start_record.setStyleSheet(self.get_button_style("#f44336"))
        
        self.btn_stop_record = QPushButton("停止录制")
        self.btn_stop_record.setEnabled(False)
        self.btn_stop_record.setStyleSheet(self.get_button_style("#ff9800"))
        
        record_layout.addWidget(self.btn_start_record)
        record_layout.addWidget(self.btn_stop_record)
        layout.addLayout(record_layout)
        
        # 视频文件控制（仅视频文件时显示）
        self.video_control_widget = QWidget()
        video_control_layout = QVBoxLayout(self.video_control_widget)
        
        self.video_progress_slider = QSlider(Qt.Horizontal)
        self.video_progress_slider.setEnabled(False)
        self.video_progress_slider.setMinimum(0)
        self.video_progress_slider.setMaximum(100)
        video_control_layout.addWidget(QLabel("视频进度:"))
        video_control_layout.addWidget(self.video_progress_slider)
        
        # 播放控制按钮
        video_button_layout = QHBoxLayout()
        self.btn_play_pause = QPushButton("播放/暂停")
        self.btn_play_pause.setEnabled(False)
        self.btn_play_pause.setStyleSheet(self.get_button_style("#4CAF50"))
        
        self.btn_video_reset = QPushButton("重置")
        self.btn_video_reset.setEnabled(False)
        self.btn_video_reset.setStyleSheet(self.get_button_style("#FF9800"))
        
        video_button_layout.addWidget(self.btn_play_pause)
        video_button_layout.addWidget(self.btn_video_reset)
        video_control_layout.addLayout(video_button_layout)
        
        # 播放状态显示
        self.lbl_play_status = QLabel("播放状态: 已暂停")
        self.lbl_play_status.setFont(QFont("Arial", 9))
        video_control_layout.addWidget(self.lbl_play_status)
        
        layout.addWidget(self.video_control_widget)
        self.video_control_widget.hide()  # 默认隐藏
        
        group.setLayout(layout)
        return group
        
    def create_vlm_control_group(self):
        """创建VLM控制组"""
        group = QGroupBox("VLM处理控制")
        layout = QVBoxLayout()
        
        # 提示词输入 - 使用专门的中文输入组件
        layout.addWidget(QLabel("提示词:"))
        self.prompt_input = ChineseInputLineEdit()
        self.prompt_input.setMinimumHeight(40)
        self.prompt_input.setPlaceholderText("请输入您的问题或指令...")
        
        layout.addWidget(self.prompt_input)
        
        # 处理按钮
        process_layout = QHBoxLayout()
        self.btn_process_current = QPushButton("分析当前画面")
        self.btn_process_current.setEnabled(False)
        self.btn_process_current.setStyleSheet(self.get_button_style("#9C27B0"))
        
        self.btn_process_video = QPushButton("分析整个视频")
        self.btn_process_video.setEnabled(False)
        self.btn_process_video.setStyleSheet(self.get_button_style("#607D8B"))
        
        process_layout.addWidget(self.btn_process_current)
        process_layout.addWidget(self.btn_process_video)
        layout.addLayout(process_layout)
        
        # VLM状态显示
        self.vlm_status_label = QLabel("VLM状态: 正在加载模型...")
        self.vlm_status_label.setFont(QFont("Arial", 10))
        layout.addWidget(self.vlm_status_label)
        
        # 进度条
        self.vlm_progress = QProgressBar()
        self.vlm_progress.setVisible(False)
        layout.addWidget(self.vlm_progress)
        
        group.setLayout(layout)
        return group
        
    def create_status_group(self):
        """创建状态信息组"""
        group = QGroupBox("系统状态")
        layout = QVBoxLayout()
        
        self.lbl_input_status = QLabel("输入源: 未连接")
        self.lbl_input_status.setFont(QFont("Arial", 10))
        
        self.lbl_recording_status = QLabel("录制状态: 未开始")
        self.lbl_recording_status.setFont(QFont("Arial", 10))
        
        self.lbl_recording_time = QLabel("录制时长: 00:00:00")
        self.lbl_recording_time.setFont(QFont("Arial", 10))
        
        self.lbl_input_info = QLabel("输入信息: -")
        self.lbl_input_info.setFont(QFont("Arial", 9))
        self.lbl_input_info.setWordWrap(True)
        
        layout.addWidget(self.lbl_input_status)
        layout.addWidget(self.lbl_recording_status)
        layout.addWidget(self.lbl_recording_time)
        layout.addWidget(self.lbl_input_info)
        
        group.setLayout(layout)
        return group
        
    def create_output_group(self):
        """创建VLM输出显示组"""
        group = QGroupBox("VLM分析结果")
        layout = QVBoxLayout()
        
        # 创建可滚动的文本显示区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(200)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Microsoft YaHei", 10))
        scroll_area.setWidget(self.output_text)
        
        layout.addWidget(scroll_area)
        
        # 输出控制按钮
        output_control_layout = QHBoxLayout()
        self.btn_clear_output = QPushButton("清空输出")
        self.btn_copy_output = QPushButton("复制文本")
        
        output_control_layout.addWidget(self.btn_clear_output)
        output_control_layout.addWidget(self.btn_copy_output)
        layout.addLayout(output_control_layout)
        
        group.setLayout(layout)
        return group
        
    def create_tts_control_group(self):
        """创建语音控制组"""
        group = QGroupBox("语音输出控制")
        layout = QVBoxLayout()
        
        # 语音控制按钮
        self.btn_speak_output = QPushButton("朗读分析结果")
        self.btn_speak_output.setEnabled(False)
        self.btn_speak_output.setStyleSheet(self.get_button_style("#FF5722"))
        
        layout.addWidget(self.btn_speak_output)
        
        # 语音设置
        self.lbl_tts_status = QLabel("语音状态: 就绪")
        self.lbl_tts_status.setFont(QFont("Arial", 9))
        layout.addWidget(self.lbl_tts_status)
        
        group.setLayout(layout)
        return group
        
    def create_history_group(self):
        """创建历史记录组"""
        group = QGroupBox("处理历史")
        layout = QVBoxLayout()
        
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        self.history_text.setMaximumHeight(150)
        self.history_text.setFont(QFont("Arial", 8))
        layout.addWidget(self.history_text)
        
        group.setLayout(layout)
        return group
    
    def get_button_style(self, bg_color):
        """获取按钮样式"""
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                font-size: 12px;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {bg_color}DD;
            }}
            QPushButton:disabled {{
                background-color: #cccccc;
                color: #666666;
            }}
        """
        
    def connect_signals(self):
        """连接信号槽"""
        # 输入源控制
        self.btn_open_camera.clicked.connect(self.on_open_camera)
        self.btn_open_video.clicked.connect(self.on_open_video_file)
        self.btn_start_record.clicked.connect(self.on_start_record)
        self.btn_stop_record.clicked.connect(self.on_stop_record)
        self.btn_play_pause.clicked.connect(self.on_play_pause)
        self.btn_video_reset.clicked.connect(self.on_video_reset)
        self.video_progress_slider.valueChanged.connect(self.on_video_progress_changed)
        self.video_progress_slider.sliderPressed.connect(self.on_slider_pressed)
        self.video_progress_slider.sliderReleased.connect(self.on_slider_released)
        
        # VLM处理
        self.btn_process_current.clicked.connect(self.on_process_current_frame)
        self.btn_process_video.clicked.connect(self.on_process_video_file)
        
        # 输出控制
        self.btn_clear_output.clicked.connect(self.output_text.clear)
        self.btn_copy_output.clicked.connect(self.on_copy_output)
        
        # 语音控制
        self.btn_speak_output.clicked.connect(self.on_speak_output)
        
        # 输入控制器信号
        self.input_controller.frame_ready.connect(self.camera_widget.update_frame)
        self.input_controller.status_changed.connect(self.on_input_status_changed)
        self.input_controller.recording_time_updated.connect(self.on_recording_time_updated)
        self.input_controller.input_info_updated.connect(self.on_input_info_updated)
        self.input_controller.input_type_changed.connect(self.on_input_type_changed)
        self.input_controller.input_closed.connect(self.on_input_closed)
        
        # VLM处理器信号
        self.vlm_processor.text_generated.connect(self.on_vlm_text_generated)
        self.vlm_processor.error_occurred.connect(self.on_vlm_error)
        self.vlm_processor.model_loaded.connect(self.on_vlm_model_loaded)
        self.vlm_processor.loading_progress.connect(self.on_vlm_loading_progress)
        
        # TTS处理器信号
        self.tts_processor.speech_started.connect(self.on_speech_started)
        self.tts_processor.speech_finished.connect(self.on_speech_finished)
        self.tts_processor.error_occurred.connect(self.on_tts_error)
        
    def load_vlm_model(self):
        """加载VLM模型"""
        self.vlm_progress.setVisible(True)
        self.vlm_progress.setRange(0, 0)  # 不确定进度
        self.vlm_processor.load_model()
        
    def on_open_camera(self):
        """打开/关闭摄像头"""
        if self.input_controller.is_input_opened() and self.input_controller.get_input_type() == "camera":
            # 关闭摄像头
            self.input_controller.close_input()
            self.btn_open_camera.setText("打开摄像头")
            self.btn_start_record.setEnabled(False)
            self.btn_process_current.setEnabled(False)
            # clear_display由input_closed信号自动调用
        else:
            # 打开摄像头
            if self.input_controller.open_camera():
                self.btn_open_camera.setText("关闭摄像头")
                self.btn_start_record.setEnabled(True)
                if self.vlm_processor.is_model_loaded:
                    self.btn_process_current.setEnabled(True)
            else:
                QMessageBox.critical(self, "错误", "无法打开摄像头！")
                
    def on_open_video_file(self):
        """打开视频文件"""
        if self.input_controller.is_input_opened() and self.input_controller.get_input_type() == "video":
            # 关闭视频文件
            self.input_controller.close_input()
            self.btn_open_video.setText("打开视频文件")
            self.current_video_path = None
            # clear_display由input_closed信号自动调用
        else:
            # 选择视频文件
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择视频文件", "", 
                "视频文件 (*.mp4 *.avi *.mov *.mkv *.flv *.wmv *.webm *.m4v);;所有文件 (*)"
            )
            
            if file_path:
                if self.input_controller.open_video_file(file_path):
                    self.btn_open_video.setText("关闭视频文件")
                    self.current_video_path = file_path
                    if self.vlm_processor.is_model_loaded:
                        self.btn_process_current.setEnabled(True)
                        self.btn_process_video.setEnabled(True)
                else:
                    QMessageBox.critical(self, "错误", "无法打开视频文件！")
    
    def on_start_record(self):
        """开始录制"""
        filename = self.data_manager.generate_filename()
        if self.input_controller.start_recording(filename):
            self.btn_start_record.setEnabled(False)
            self.btn_stop_record.setEnabled(True)
            self.lbl_recording_status.setText("录制状态: 正在录制")
            
    def on_stop_record(self):
        """停止录制"""
        metadata = self.input_controller.stop_recording()
        if metadata:
            self.btn_start_record.setEnabled(True)
            self.btn_stop_record.setEnabled(False)
            self.lbl_recording_status.setText("录制状态: 已停止")
            self.lbl_recording_time.setText("录制时长: 00:00:00")
            
            # 保存元数据
            self.data_manager.save_metadata(metadata)
            self.update_history()
    
    def on_play_pause(self):
        """播放/暂停视频"""
        is_playing = self.input_controller.toggle_play_pause()
        if is_playing:
            self.lbl_play_status.setText("播放状态: 正在播放")
        else:
            self.lbl_play_status.setText("播放状态: 已暂停")
    
    def on_video_reset(self):
        """重置视频"""
        if self.input_controller.reset_video():
            self.video_progress_slider.setValue(0)
            self.lbl_play_status.setText("播放状态: 已暂停")
    
    def on_video_progress_changed(self, value):
        """视频进度条改变"""
        if hasattr(self, '_slider_being_dragged') and self._slider_being_dragged:
            return  # 如果正在拖拽，不处理
            
        # 将进度条的值转换为视频时间（假设视频总时长已知）
        if hasattr(self.input_controller, 'seek_to_progress'):
            progress = value / 100.0  # 转换为0-1的比例
            self.input_controller.seek_to_progress(progress)
    
    def on_slider_pressed(self):
        """进度条开始拖拽"""
        self._slider_being_dragged = True
        # 暂停视频以便精确定位
        if hasattr(self.input_controller, 'pause_playback'):
            self.input_controller.pause_playback()
    
    def on_slider_released(self):
        """进度条拖拽结束"""
        self._slider_being_dragged = False
        # 跳转到指定位置
        value = self.video_progress_slider.value()
        progress = value / 100.0
        if hasattr(self.input_controller, 'seek_to_progress'):
            self.input_controller.seek_to_progress(progress)
        # 恢复播放
        if hasattr(self.input_controller, 'resume_playback'):
            self.input_controller.resume_playback()
            self.lbl_play_status.setText("播放状态: 正在播放")
    
    def on_process_current_frame(self):
        """处理当前帧"""
        if self.is_vlm_processing:
            QMessageBox.information(self, "提示", "VLM正在处理中，请稍候...")
            return
            
        frame = self.input_controller.get_current_frame()
        if frame is not None:
            prompt = self.prompt_input.text().strip()
            if not prompt:
                prompt = "请描述这个画面的内容"
                
            self.is_vlm_processing = True
            self.btn_process_current.setEnabled(False)
            self.vlm_status_label.setText("VLM状态: 正在处理当前画面...")
            
            self.vlm_processor.process_frame(frame, prompt)
    
    def on_process_video_file(self):
        """处理整个视频文件"""
        if not self.current_video_path:
            QMessageBox.warning(self, "警告", "请先打开视频文件")
            return
            
        if self.is_vlm_processing:
            QMessageBox.information(self, "提示", "VLM正在处理中，请稍候...")
            return
            
        prompt = self.prompt_input.text().strip()
        if not prompt:
            prompt = "请详细描述这个视频的内容和主要场景"
            
        self.is_vlm_processing = True
        self.btn_process_video.setEnabled(False)
        self.vlm_status_label.setText("VLM状态: 正在处理视频文件...")
        
        self.vlm_processor.process_video(self.current_video_path, prompt)
    
    def on_copy_output(self):
        """复制输出文本"""
        text = self.output_text.toPlainText()
        if text:
            from PyQt5.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            QMessageBox.information(self, "提示", "文本已复制到剪贴板")
    
    def on_speak_output(self):
        """朗读输出文本"""
        text = self.output_text.toPlainText()
        if text.strip():
            self.tts_processor.speak(text)
        else:
            QMessageBox.information(self, "提示", "没有可朗读的内容")
    
    
    # 信号处理方法
    def on_input_status_changed(self, status):
        """输入源状态改变"""
        self.lbl_input_status.setText(f"输入源: {status}")
        
    def on_recording_time_updated(self, time_str):
        """更新录制时间"""
        self.lbl_recording_time.setText(f"录制时长: {time_str}")
        
    def on_input_info_updated(self, info):
        """更新输入源信息"""
        if 'type' in info:
            info_text = f"类型: {info['type']}"
            if 'resolution' in info:
                info_text += f"\n分辨率: {info['resolution']}"
            if 'fps' in info:
                info_text += f"\nFPS: {info['fps']}"
            if 'current_time' in info and info['type'] == 'video_file':
                info_text += f"\n当前时间: {info['current_time']:.1f}s"
            
            self.lbl_input_info.setText(info_text)
    
    def on_input_type_changed(self, input_type):
        """输入类型改变"""
        if input_type == "video":
            self.video_control_widget.show()
            self.btn_play_pause.setEnabled(True)
            self.btn_video_reset.setEnabled(True)
            self.video_progress_slider.setEnabled(True)
            self.lbl_play_status.setText("播放状态: 已暂停")  # 视频打开时默认暂停
            self.btn_play_pause.setText("播放")  # 按钮显示为播放
            if self.vlm_processor.is_model_loaded:
                self.btn_process_video.setEnabled(True)
        else:
            self.video_control_widget.hide()
            self.btn_process_video.setEnabled(False)
            
        # 根据输入类型和VLM状态启用按钮
        if self.vlm_processor.is_model_loaded and input_type in ["camera", "video"]:
            self.btn_process_current.setEnabled(True)
    
    def on_input_closed(self):
        """输入源关闭时清空显示"""
        self.camera_widget.clear_display()  # 清空显示，恢复黑屏
        # 禁用相关按钮
        self.btn_process_current.setEnabled(False)
        self.btn_process_video.setEnabled(False)
        self.video_control_widget.hide()
    
    def on_vlm_text_generated(self, text):
        """VLM文本生成完成"""
        self.is_vlm_processing = False
        self.vlm_status_label.setText("VLM状态: 就绪")
        
        # 启用相关按钮
        if self.input_controller.is_input_opened():
            self.btn_process_current.setEnabled(True)
            if self.input_controller.get_input_type() == "video":
                self.btn_process_video.setEnabled(True)
        
        # 显示结果
        self.output_text.moveCursor(QTextCursor.End)
        self.output_text.insertPlainText(f"\n{text}\n")
        
        # 启用朗读按钮
        self.btn_speak_output.setEnabled(True)
        
    
    def on_vlm_error(self, error_msg):
        """VLM处理错误"""
        self.is_vlm_processing = False
        self.vlm_status_label.setText("VLM状态: 错误")
        
        # 启用相关按钮
        if self.input_controller.is_input_opened():
            self.btn_process_current.setEnabled(True)
            if self.input_controller.get_input_type() == "video":
                self.btn_process_video.setEnabled(True)
        
        QMessageBox.critical(self, "VLM处理错误", error_msg)
    
    def on_vlm_model_loaded(self):
        """VLM模型加载完成"""
        self.vlm_status_label.setText("VLM状态: 就绪")
        self.vlm_progress.setVisible(False)
        
        # 如果有输入源，启用处理按钮
        if self.input_controller.is_input_opened():
            self.btn_process_current.setEnabled(True)
            if self.input_controller.get_input_type() == "video":
                self.btn_process_video.setEnabled(True)
    
    def on_vlm_loading_progress(self, message):
        """VLM加载进度"""
        self.vlm_status_label.setText(f"VLM状态: {message}")
    
    def on_speech_started(self):
        """开始朗读"""
        self.btn_speak_output.setEnabled(False)
        self.lbl_tts_status.setText("语音状态: 正在朗读...")
    
    def on_speech_finished(self):
        """朗读完成"""
        self.btn_speak_output.setEnabled(True)
        self.lbl_tts_status.setText("语音状态: 就绪")
    
    def on_tts_error(self, error_msg):
        """TTS错误"""
        self.btn_speak_output.setEnabled(True)
        self.lbl_tts_status.setText("语音状态: 错误")
        QMessageBox.warning(self, "语音输出错误", error_msg)
    
    def add_to_history(self, message):
        """添加到历史记录"""
        self.history_text.append(message)
    
    def update_history(self):
        """更新录制历史"""
        history = self.data_manager.get_recording_history()
        history_text = ""
        for record in history[-5:]:  # 显示最近5条
            history_text += f"文件: {record['filename']}\n"
            history_text += f"时间: {record['timestamp']}\n"
            history_text += f"时长: {record['duration']}秒\n\n"
        self.history_text.setText(history_text)
        
    def inputMethodEvent(self, event):
        """处理输入法事件"""
        # 让输入法事件传递给焦点组件
        if self.prompt_input.hasFocus():
            self.prompt_input.inputMethodEvent(event)
        else:
            super().inputMethodEvent(event)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.input_controller.is_recording():
            reply = QMessageBox.question(self, '确认', '正在录制中，确定要退出吗？',
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                event.ignore()
                return
                
        # 清理资源
        self.input_controller.close_input()
        self.vlm_processor.stop_processing()
        self.tts_processor.stop_speaking()
        
        event.accept()