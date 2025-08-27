"""
VLM远程处理器 - 基于现有VLMProcessor修改为客户端模式
连接到远程VLM服务器进行推理
"""
import os
import json
import base64
import io
import asyncio
import logging
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PIL import Image
import websockets.asyncio.client as client

logger = logging.getLogger(__name__)


class VLMRemoteWorker(QThread):
    """VLM远程处理工作线程 - 替代原有的VLMWorker"""
    text_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, host="localhost", port=8000):
        super().__init__()
        self.host = host
        self.port = port
        self.messages = None
        self.processing_type = "image"  # "image" 或 "video"
        self.video_path = None
        self.prompt = None
        
    def set_image_messages(self, messages):
        """设置图像处理消息"""
        self.messages = messages
        self.processing_type = "image"
        
    def set_video_processing(self, video_path, prompt):
        """设置视频处理参数"""
        self.video_path = video_path
        self.prompt = prompt
        self.processing_type = "video"
    
    def run(self):
        """执行远程VLM推理"""
        try:
            # 运行异步任务
            asyncio.run(self._process_async())
        except Exception as e:
            self.error_occurred.emit(f"远程VLM处理错误: {str(e)}")
    
    async def _process_async(self):
        """异步处理方法"""
        try:
            # 连接到服务器
            uri = f"ws://{self.host}:{self.port}"
            async with client.connect(uri) as websocket:
                # 接收服务器元数据
                metadata_msg = await websocket.recv()
                metadata = json.loads(metadata_msg)
                print(f"连接到VLM服务器: {metadata}")
                
                if self.processing_type == "video":
                    # 视频处理 - 读取本地视频文件并传输到服务器
                    import os
                    if not os.path.exists(self.video_path):
                        raise ValueError(f"视频文件不存在: {self.video_path}")
                    
                    # 读取视频文件内容并编码为base64
                    with open(self.video_path, 'rb') as f:
                        video_data = base64.b64encode(f.read()).decode('utf-8')
                    
                    # 获取文件名
                    video_filename = os.path.basename(self.video_path)
                    
                    request = {
                        "type": "video",
                        "video_data": video_data,
                        "video_filename": video_filename,
                        "prompt": self.prompt
                    }
                    
                elif self.processing_type == "image" and self.messages:
                    # 图像处理 - 从messages中提取图像和文本
                    image = None
                    prompt = ""
                    
                    for message in self.messages:
                        if message["role"] == "user":
                            for content in message["content"]:
                                if content["type"] == "text":
                                    prompt = content["text"]
                                elif content["type"] == "image":
                                    image = content["image"]
                    
                    if image is None:
                        raise ValueError("未找到图像数据")
                    
                    # 将PIL图像编码为base64
                    buffer = io.BytesIO()
                    image.save(buffer, format='PNG')
                    image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
                    
                    request = {
                        "type": "image",
                        "image_data": image_data,
                        "prompt": prompt
                    }
                else:
                    raise ValueError("没有有效的输入数据")
                
                # 发送请求
                await websocket.send(json.dumps(request))
                
                # 接收响应
                response_msg = await websocket.recv()
                response = json.loads(response_msg)
                
                if "error" in response:
                    raise RuntimeError(f"服务器错误: {response['error']}")
                
                # 发射结果信号
                self.text_ready.emit(response["result"])
                
        except Exception as e:
            self.error_occurred.emit(f"远程连接错误: {str(e)}")


class VLMRemoteProcessor(QObject):
    """VLM远程处理器主类 - 替代原有的VLMProcessor"""
    
    text_generated = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    model_loaded = pyqtSignal()
    loading_progress = pyqtSignal(str)
    
    def __init__(self, server_host="localhost", server_port=8000):
        super().__init__()
        self.server_host = server_host
        self.server_port = server_port
        self.worker = None
        self.is_model_loaded = False
        
    def load_model(self):
        """连接到远程服务器 - 替代模型加载"""
        try:
            self.loading_progress.emit("连接到远程VLM服务器...")
            
            # 测试连接
            asyncio.run(self._test_connection())
            
            self.is_model_loaded = True
            self.model_loaded.emit()
            self.loading_progress.emit("远程VLM服务器连接成功")
            print("远程VLM连接成功！")
            
        except Exception as e:
            error_msg = f"连接远程服务器失败: {str(e)}"
            print(error_msg)
            self.error_occurred.emit(error_msg)
    
    async def _test_connection(self):
        """测试连接"""
        uri = f"ws://{self.server_host}:{self.server_port}"
        async with client.connect(uri) as websocket:
            metadata_msg = await websocket.recv()
            metadata = json.loads(metadata_msg)
            print(f"服务器信息: {metadata}")
    
    def process_image(self, messages):
        """处理图像 - 通过远程服务器"""
        if not self.is_model_loaded:
            self.error_occurred.emit("远程服务器未连接")
            return
        
        # 停止之前的工作线程
        if self.worker and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()
        
        # 创建新的远程工作线程
        self.worker = VLMRemoteWorker(self.server_host, self.server_port)
        self.worker.text_ready.connect(self.text_generated.emit)
        self.worker.error_occurred.connect(self.error_occurred.emit)
        
        # 设置图像处理任务
        self.worker.set_image_messages(messages)
        self.worker.start()
    
    def process_video(self, video_path, prompt):
        """处理视频 - 通过远程服务器"""
        if not self.is_model_loaded:
            self.error_occurred.emit("远程服务器未连接")
            return
        
        # 停止之前的工作线程
        if self.worker and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()
        
        # 创建新的远程工作线程
        self.worker = VLMRemoteWorker(self.server_host, self.server_port)
        self.worker.text_ready.connect(self.text_generated.emit)
        self.worker.error_occurred.connect(self.error_occurred.emit)
        
        # 设置视频处理任务
        self.worker.set_video_processing(video_path, prompt)
        self.worker.start()
    
    def process_frame(self, frame, prompt):
        """处理单帧图像 - 通过远程服务器"""
        # 将numpy数组转换为PIL图像
        from PIL import Image
        if hasattr(frame, 'shape'):
            # numpy数组格式
            if len(frame.shape) == 3:
                image = Image.fromarray(frame)
            else:
                raise ValueError("不支持的图像格式")
        else:
            # 假设已经是PIL图像
            image = frame
        
        # 构建消息格式
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image", "image": image},
            ]}
        ]
        
        # 调用图像处理
        self.process_image(messages)