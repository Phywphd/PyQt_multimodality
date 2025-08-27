#!/usr/bin/env python3
"""
VLM模型服务器端
在有48GB显存的服务器上运行，为客户端提供VLM推理服务
"""
import asyncio
import base64
import io
import json
import logging
import time
import traceback
from typing import Dict, Any

import torch
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
from PIL import Image
import websockets.asyncio.server as server
import websockets.frames


logger = logging.getLogger(__name__)


class VLMServer:
    """VLM模型服务器"""
    
    def __init__(self, model_path: str = "Qwen/Qwen2.5-VL-7B-Instruct", host: str = "0.0.0.0", port: int = 8000):
        self.model_path = model_path
        self.host = host
        self.port = port
        self.model = None
        self.processor = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        logging.getLogger("websockets.server").setLevel(logging.INFO)
        
    def load_model(self):
        """加载VLM模型"""
        print(f"正在加载模型: {self.model_path}")
        
        # 检查GPU
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"使用设备: {device}")
        
        if device == "cuda":
            gpu_count = torch.cuda.device_count()
            print(f"可用GPU数量: {gpu_count}")
            for i in range(gpu_count):
                gpu_name = torch.cuda.get_device_name(i)
                gpu_memory = torch.cuda.get_device_properties(i).total_memory / 1024**3
                print(f"GPU {i}: {gpu_name} ({gpu_memory:.1f} GB)")
        
        # 加载模型 - 使用服务器的全部GPU内存
        load_kwargs = {
            "torch_dtype": torch.bfloat16,
            "device_map": "auto",  # 自动分配到多个GPU
            "trust_remote_code": True,
        }
        
        # 尝试使用Flash Attention 2
        try:
            import flash_attn
            load_kwargs["attn_implementation"] = "flash_attention_2"
            print("使用Flash Attention 2优化")
        except ImportError:
            print("Flash Attention 2不可用，使用标准attention")
        
        print(f"模型加载配置: {load_kwargs}")
        
        self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            self.model_path, **load_kwargs
        )
        self.processor = AutoProcessor.from_pretrained(self.model_path)
        
        print("VLM模型加载完成!")
        
    def process_image(self, image_data: str, prompt: str) -> str:
        """处理图像推理"""
        try:
            # 解码base64图像
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # 构建消息
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image", "image": image},
                ]}
            ]
            
            # 处理输入
            text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            image_inputs, video_inputs = process_vision_info(messages)
            
            inputs = self.processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt"
            )
            inputs = inputs.to(self.model.device)
            
            # 生成回复
            with torch.no_grad():
                generated_ids = self.model.generate(**inputs, max_new_tokens=512)
                generated_ids_trimmed = [
                    out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
                ]
                output_text = self.processor.batch_decode(
                    generated_ids_trimmed, 
                    skip_special_tokens=True, 
                    clean_up_tokenization_spaces=False
                )
                
            return output_text[0].strip()
            
        except Exception as e:
            logger.error(f"图像处理错误: {e}")
            return f"处理错误: {str(e)}"
    
    def process_video_from_data(self, video_data: str, video_filename: str, prompt: str) -> str:
        """从base64数据处理视频推理"""
        try:
            # 保存视频文件到临时目录
            import tempfile
            import os
            
            temp_dir = tempfile.mkdtemp()
            video_path = os.path.join(temp_dir, video_filename)
            
            # 解码并保存视频文件
            video_bytes = base64.b64decode(video_data)
            with open(video_path, 'wb') as f:
                f.write(video_bytes)
            
            print(f"视频文件已保存到: {video_path}")
            
            # 构建消息 - 按照cookbook格式
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"video": video_path, "total_pixels": 20480 * 28 * 28, "min_pixels": 16 * 28 * 28},
                ]}
            ]
            
            # 处理输入
            text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            image_inputs, video_inputs, video_kwargs = process_vision_info([messages], return_video_kwargs=True)
            fps_inputs = video_kwargs['fps']
            
            inputs = self.processor(
                text=[text], 
                images=image_inputs, 
                videos=video_inputs, 
                fps=fps_inputs, 
                padding=True, 
                return_tensors="pt"
            )
            inputs = inputs.to(self.model.device)
            
            # 生成回复
            with torch.no_grad():
                output_ids = self.model.generate(**inputs, max_new_tokens=2048)
                generated_ids = [output_ids[len(input_ids):] for input_ids, output_ids in zip(inputs.input_ids, output_ids)]
                output_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True)
            
            result = output_text[0].strip()
            
            # 清理临时文件
            try:
                import shutil
                shutil.rmtree(temp_dir)
                print(f"清理临时目录: {temp_dir}")
            except:
                pass
                
            return result
            
        except Exception as e:
            # 确保清理临时文件
            try:
                import shutil
                if 'temp_dir' in locals():
                    shutil.rmtree(temp_dir)
            except:
                pass
            logger.error(f"视频处理错误: {e}")
            return f"处理错误: {str(e)}"
    
    def process_video(self, video_path: str, prompt: str) -> str:
        """处理视频推理（兼容旧接口）"""
        try:
            # 构建消息 - 按照cookbook格式
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"video": video_path, "total_pixels": 20480 * 28 * 28, "min_pixels": 16 * 28 * 28},
                ]}
            ]
            
            # 处理输入
            text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            image_inputs, video_inputs, video_kwargs = process_vision_info([messages], return_video_kwargs=True)
            fps_inputs = video_kwargs['fps']
            
            inputs = self.processor(
                text=[text], 
                images=image_inputs, 
                videos=video_inputs, 
                fps=fps_inputs, 
                padding=True, 
                return_tensors="pt"
            )
            inputs = inputs.to(self.model.device)

            # 生成回复
            with torch.no_grad():
                output_ids = self.model.generate(**inputs, max_new_tokens=2048)
                generated_ids = [output_ids[len(input_ids):] for input_ids, output_ids in zip(inputs.input_ids, output_ids)]
                output_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True)
                
            return output_text[0].strip()
            
        except Exception as e:
            logger.error(f"视频处理错误: {e}")
            return f"处理错误: {str(e)}"
    
    async def handle_client(self, websocket):
        """处理客户端连接"""
        logger.info(f"客户端连接: {websocket.remote_address}")
        
        # 发送服务器元数据
        metadata = {
            "model_path": self.model_path,
            "device": str(self.model.device) if self.model else "未加载",
            "status": "ready"
        }
        await websocket.send(json.dumps(metadata))
        
        try:
            async for message in websocket:
                start_time = time.time()
                
                try:
                    # 解析请求
                    request = json.loads(message)
                    request_type = request.get("type", "")
                    
                    if request_type == "image":
                        # 图像处理
                        image_data = request["image_data"]
                        prompt = request["prompt"]
                        result = self.process_image(image_data, prompt)
                        
                    elif request_type == "video":
                        # 视频处理 - 支持路径和数据两种方式
                        if "video_data" in request:
                            # 从客户端传输的视频数据
                            video_data = request["video_data"]
                            video_filename = request["video_filename"]
                            prompt = request["prompt"]
                            result = self.process_video_from_data(video_data, video_filename, prompt)
                        else:
                            # 视频路径（保持兼容性）
                            video_path = request["video_path"]
                            prompt = request["prompt"]
                            result = self.process_video(video_path, prompt)
                        
                    else:
                        result = f"不支持的请求类型: {request_type}"
                    
                    # 发送响应
                    processing_time = time.time() - start_time
                    response = {
                        "result": result,
                        "processing_time_ms": processing_time * 1000,
                        "timestamp": time.time()
                    }
                    
                    await websocket.send(json.dumps(response))
                    logger.info(f"处理请求完成: {processing_time:.2f}s")
                    
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({"error": "Invalid JSON format"}))
                except Exception as e:
                    error_msg = f"处理错误: {str(e)}"
                    logger.error(error_msg)
                    await websocket.send(json.dumps({"error": error_msg}))
                    
        except websockets.ConnectionClosed:
            logger.info(f"客户端断开连接: {websocket.remote_address}")
        except Exception as e:
            logger.error(f"连接错误: {e}")
    
    def serve_forever(self):
        """启动服务器"""
        print(f"启动VLM服务器在 {self.host}:{self.port}")
        asyncio.run(self._run_server())
    
    async def _run_server(self):
        """运行服务器"""
        async with server.serve(
            self.handle_client,
            self.host,
            self.port,
            compression=None,
            max_size=None,
        ) as ws_server:
            print(f"VLM服务器运行中: ws://{self.host}:{self.port}")
            await ws_server.serve_forever()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="VLM模型服务器")
    parser.add_argument("--model-path", default="Qwen/Qwen2.5-VL-7B-Instruct", help="模型路径")
    parser.add_argument("--host", default="0.0.0.0", help="服务器主机")
    parser.add_argument("--port", type=int, default=8000, help="服务器端口")
    
    args = parser.parse_args()
    
    # 创建并启动服务器
    vlm_server = VLMServer(args.model_path, args.host, args.port)
    vlm_server.load_model()
    vlm_server.serve_forever()


if __name__ == "__main__":
    main()