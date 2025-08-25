"""
VLM处理器 - 基于Qwen2.5-VL官方代码的视觉语言模型处理模块
参考: https://github.com/QwenLM/Qwen2.5-VL/blob/main/README.md
"""
import torch
import numpy as np
from PIL import Image
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
from PyQt5.QtCore import QObject, QThread, pyqtSignal
import cv2
import os
import tempfile


class VLMWorker(QThread):
    """VLM处理工作线程 - 基于官方推理代码"""
    text_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, model, processor):
        super().__init__()
        self.model = model
        self.processor = processor
        self.messages = None
        
    def set_messages(self, messages):
        """设置要处理的消息"""
        self.messages = messages
    
    def run(self):
        """执行VLM推理 - 严格按照官方代码"""
        try:
            if not self.messages:
                self.error_occurred.emit("没有有效的输入消息")
                return
            
            # 按照官方代码处理消息
            text = self.processor.apply_chat_template(
                self.messages, 
                tokenize=False, 
                add_generation_prompt=True
            )
            
            # 处理视觉信息
            image_inputs, video_inputs = process_vision_info(self.messages)
            
            # 准备输入
            inputs = self.processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt"
            )
            inputs = inputs.to(self.model.device)
            
            # 生成回复
            generated_ids = self.model.generate(**inputs, max_new_tokens=512)
            generated_ids_trimmed = [
                out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            output_text = self.processor.batch_decode(
                generated_ids_trimmed, 
                skip_special_tokens=True, 
                clean_up_tokenization_spaces=False
            )
            
            self.text_ready.emit(output_text[0])
            
        except Exception as e:
            self.error_occurred.emit(f"VLM处理错误: {str(e)}")


class VLMProcessor(QObject):
    """VLM处理器主类 - 基于Qwen2.5-VL官方实现"""
    
    text_generated = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    model_loaded = pyqtSignal()
    loading_progress = pyqtSignal(str)
    
    def __init__(self, model_path="Qwen/Qwen2.5-VL-3B-Instruct"):
        super().__init__()
        self.model_path = model_path
        self.model = None
        self.processor = None
        self.worker = None
        self.is_model_loaded = False
        
    def load_model(self):
        """加载VLM模型 - 按照官方推荐配置"""
        try:
            self.loading_progress.emit("正在加载模型...")
            
            # 按照官方代码加载模型
            self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                self.model_path,
                torch_dtype="auto",  # 官方推荐使用auto
                device_map="auto"
            )
            
            self.loading_progress.emit("正在加载处理器...")
            self.processor = AutoProcessor.from_pretrained(self.model_path)
            
            self.is_model_loaded = True
            self.model_loaded.emit()
            self.loading_progress.emit("模型加载完成")
            
        except Exception as e:
            error_msg = f"模型加载失败: {str(e)}"
            self.error_occurred.emit(error_msg)
    
    def process_image(self, image_path, prompt="请描述这张图片"):
        """处理图像 - 按照官方单图像推理格式"""
        if not self.is_model_loaded:
            self.error_occurred.emit("模型未加载")
            return
        
        # 按照官方格式构建消息
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image", 
                        "image": image_path
                    },
                    {"type": "text", "text": prompt}
                ]
            }
        ]
        
        self._run_inference(messages)
    
    def process_frame(self, frame, prompt="请描述这个画面"):
        """处理OpenCV帧"""
        if not self.is_model_loaded:
            self.error_occurred.emit("模型未加载")
            return
        
        # 将OpenCV帧保存为临时图像文件
        try:
            # BGR转RGB
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                frame_rgb = frame
                
            pil_image = Image.fromarray(frame_rgb)
            
            # 保存临时文件
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                pil_image.save(tmp_file.name)
                temp_path = tmp_file.name
            
            # 处理图像
            self.process_image(temp_path, prompt)
            
            # 清理临时文件 (延迟删除，在处理完成后删除)
            self._temp_file_to_cleanup = temp_path
            
        except Exception as e:
            self.error_occurred.emit(f"帧处理错误: {str(e)}")
    
    def process_video(self, video_path, prompt="请描述这个视频的内容"):
        """处理视频文件 - 按照官方视频推理格式"""
        if not self.is_model_loaded:
            self.error_occurred.emit("模型未加载")
            return
        
        # 按照官方格式构建视频消息
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "video", 
                        "video": video_path,
                        "total_pixels": 20480 * 28 * 28,  # 官方推荐配置
                        "min_pixels": 16 * 28 * 28
                    },
                    {"type": "text", "text": prompt}
                ]
            }
        ]
        
        self._run_inference(messages)
    
    def _run_inference(self, messages):
        """运行推理"""
        # 停止之前的处理
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        
        # 创建新的工作线程
        self.worker = VLMWorker(self.model, self.processor)
        self.worker.text_ready.connect(self._on_text_ready)
        self.worker.error_occurred.connect(self.error_occurred.emit)
        
        self.worker.set_messages(messages)
        self.worker.start()
    
    def _on_text_ready(self, text):
        """处理完成回调"""
        # 清理临时文件
        if hasattr(self, '_temp_file_to_cleanup') and os.path.exists(self._temp_file_to_cleanup):
            try:
                os.unlink(self._temp_file_to_cleanup)
                delattr(self, '_temp_file_to_cleanup')
            except:
                pass
        
        self.text_generated.emit(text)
    
    def is_busy(self):
        """检查是否正在处理"""
        return self.worker and self.worker.isRunning()
    
    def stop_processing(self):
        """停止当前处理"""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()