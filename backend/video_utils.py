"""
视频处理工具 - 基于Qwen2.5-VL cookbook的视频帧提取和处理
参考: /home/hyp/research/multimodal_demo/Qwen2.5-VL/cookbooks/video_understanding.ipynb
"""
import os
import math
import hashlib
import numpy as np
from PIL import Image
import decord
from decord import VideoReader, cpu


def get_video_frames(video_path, num_frames=64, cache_dir='.cache'):
    """
    提取视频关键帧 - 完全按照cookbook实现
    
    Args:
        video_path: 视频文件路径
        num_frames: 要提取的帧数
        cache_dir: 缓存目录
        
    Returns:
        tuple: (video_file_path, frames, timestamps)
    """
    os.makedirs(cache_dir, exist_ok=True)

    # 生成视频hash用于缓存
    video_hash = hashlib.md5(video_path.encode('utf-8')).hexdigest()
    video_file_path = video_path

    # 缓存文件路径
    frames_cache_file = os.path.join(cache_dir, f'{video_hash}_{num_frames}_frames.npy')
    timestamps_cache_file = os.path.join(cache_dir, f'{video_hash}_{num_frames}_timestamps.npy')

    # 检查缓存
    if os.path.exists(frames_cache_file) and os.path.exists(timestamps_cache_file):
        print(f"Loading cached frames for {video_path}")
        frames = np.load(frames_cache_file)
        timestamps = np.load(timestamps_cache_file)
        return video_file_path, frames, timestamps

    # 使用decord读取视频 - 按照cookbook
    print(f"Extracting {num_frames} frames from {video_path}")
    vr = VideoReader(video_file_path, ctx=cpu(0))
    total_frames = len(vr)
    
    print(f"Video has {total_frames} total frames")

    # 等间隔采样帧
    indices = np.linspace(0, total_frames - 1, num=num_frames, dtype=int)
    frames = vr.get_batch(indices).asnumpy()
    
    # 获取时间戳
    timestamps = np.array([vr.get_frame_timestamp(idx) for idx in indices])

    # 保存缓存
    np.save(frames_cache_file, frames)
    np.save(timestamps_cache_file, timestamps)
    
    print(f"Extracted frames shape: {frames.shape}")
    
    return video_file_path, frames, timestamps


def create_image_grid(images, num_columns=8):
    """
    创建图像网格显示 - 按照cookbook实现
    
    Args:
        images: numpy数组格式的图像列表
        num_columns: 每行显示的图像数
        
    Returns:
        PIL.Image: 拼接后的网格图像
    """
    pil_images = [Image.fromarray(image) for image in images]
    num_rows = math.ceil(len(images) / num_columns)

    if not pil_images:
        return None

    img_width, img_height = pil_images[0].size
    grid_width = num_columns * img_width
    grid_height = num_rows * img_height
    grid_image = Image.new('RGB', (grid_width, grid_height))

    for idx, image in enumerate(pil_images):
        row_idx = idx // num_columns
        col_idx = idx % num_columns
        position = (col_idx * img_width, row_idx * img_height)
        grid_image.paste(image, position)

    return grid_image


def inference_video_with_frames(model, processor, video_path, prompt, 
                               max_new_tokens=2048, num_frames=64,
                               total_pixels=20480 * 28 * 28, min_pixels=16 * 28 * 28):
    """
    使用提取的帧进行视频推理 - 完全按照cookbook实现
    
    Args:
        model: Qwen2.5-VL模型
        processor: 模型处理器
        video_path: 视频文件路径
        prompt: 提示词
        max_new_tokens: 最大生成token数
        num_frames: 提取帧数
        total_pixels: 总像素数配置
        min_pixels: 最小像素数配置
        
    Returns:
        str: 模型输出文本
    """
    # Step 1: 提取视频帧 - 按照cookbook
    video_file_path, frames, timestamps = get_video_frames(video_path, num_frames)
    
    # Step 2: 构建消息格式 - 完全按照cookbook
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"video": video_file_path, "total_pixels": total_pixels, "min_pixels": min_pixels},
            ]
        },
    ]
    
    # Step 3: 处理消息 - 按照cookbook
    from qwen_vl_utils import process_vision_info
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs, video_kwargs = process_vision_info([messages], return_video_kwargs=True)
    fps_inputs = video_kwargs['fps']
    
    print(f"video input: {video_inputs[0].shape}")
    num_frames_processed, _, resized_height, resized_width = video_inputs[0].shape
    num_video_tokens = int(num_frames_processed / 2 * resized_height / 28 * resized_width / 28)
    print(f"num of video tokens: {num_video_tokens}")
    
    # Step 4: 准备输入
    inputs = processor(
        text=[text], 
        images=image_inputs, 
        videos=video_inputs, 
        fps=fps_inputs, 
        padding=True, 
        return_tensors="pt"
    )
    inputs = inputs.to(model.device)

    # Step 5: 生成输出 - 按照cookbook
    output_ids = model.generate(**inputs, max_new_tokens=max_new_tokens)
    generated_ids = [output_ids[len(input_ids):] for input_ids, output_ids in zip(inputs.input_ids, output_ids)]
    output_text = processor.batch_decode(generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True)
    
    return output_text[0]