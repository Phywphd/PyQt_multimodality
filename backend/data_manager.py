"""
数据管理器 - 负责视频文件和元数据的存储管理
"""
import os
import json
from datetime import datetime
import pickle
import numpy as np


class DataManager:
    """数据管理器"""
    
    def __init__(self, base_path='./data'):
        self.base_path = base_path
        self.video_dir = os.path.join(base_path, 'videos')
        self.metadata_dir = os.path.join(base_path, 'metadata')
        self.raw_data_dir = os.path.join(base_path, 'raw_frames')
        
        # 创建必要的目录
        self._create_directories()
        
    def _create_directories(self):
        """创建存储目录"""
        for directory in [self.video_dir, self.metadata_dir, self.raw_data_dir]:
            os.makedirs(directory, exist_ok=True)
            
    def generate_filename(self, prefix='recording'):
        """生成文件名"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.mp4"
        return os.path.join(self.video_dir, filename)
        
    def save_metadata(self, metadata):
        """
        保存元数据
        支持多种格式，便于后续不同的训练需求
        """
        if not metadata or 'filename' not in metadata:
            return
            
        # 获取基础文件名（不含扩展名）
        video_filename = os.path.basename(metadata['filename'])
        base_name = os.path.splitext(video_filename)[0]
        
        # 1. 保存为JSON格式（人类可读，便于调试）
        json_path = os.path.join(self.metadata_dir, f"{base_name}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
        # 2. 保存为pickle格式（保持Python对象完整性）
        pickle_path = os.path.join(self.metadata_dir, f"{base_name}.pkl")
        with open(pickle_path, 'wb') as f:
            pickle.dump(metadata, f)
            
        # 3. 更新总索引文件
        self._update_index(metadata)
        
    def _update_index(self, metadata):
        """更新总索引文件"""
        index_file = os.path.join(self.base_path, 'index.json')
        
        # 读取现有索引
        if os.path.exists(index_file):
            with open(index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
        else:
            index = {
                'recordings': [],
                'total_count': 0,
                'total_duration': 0
            }
            
        # 添加新记录
        record = {
            'filename': os.path.basename(metadata['filename']),
            'timestamp': metadata.get('start_time', ''),
            'duration': metadata.get('duration', 0),
            'resolution': metadata.get('camera_info', {}).get('resolution', ''),
            'fps': metadata.get('recording_params', {}).get('fps', 30)
        }
        
        index['recordings'].append(record)
        index['total_count'] += 1
        index['total_duration'] += record['duration']
        
        # 保存更新后的索引
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
            
    def save_raw_frames(self, video_filename, frames, sampling_rate=30):
        """
        保存原始帧数据（可选功能）
        用于需要逐帧处理的训练场景
        
        Args:
            video_filename: 视频文件名
            frames: 帧数据列表
            sampling_rate: 采样率（每隔多少帧保存一次）
        """
        base_name = os.path.splitext(os.path.basename(video_filename))[0]
        frame_dir = os.path.join(self.raw_data_dir, base_name)
        os.makedirs(frame_dir, exist_ok=True)
        
        # 保存采样的帧
        for i, frame in enumerate(frames):
            if i % sampling_rate == 0:
                frame_path = os.path.join(frame_dir, f"frame_{i:06d}.npy")
                np.save(frame_path, frame)
                
        # 保存帧信息
        frame_info = {
            'total_frames': len(frames),
            'saved_frames': len(frames) // sampling_rate,
            'sampling_rate': sampling_rate,
            'shape': frames[0].shape if frames else None
        }
        
        info_path = os.path.join(frame_dir, 'frame_info.json')
        with open(info_path, 'w') as f:
            json.dump(frame_info, f, indent=2)
            
    def get_recording_history(self):
        """获取录制历史"""
        index_file = os.path.join(self.base_path, 'index.json')
        
        if os.path.exists(index_file):
            with open(index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
                return index.get('recordings', [])
        
        return []
        
    def load_metadata(self, video_filename):
        """加载元数据"""
        base_name = os.path.splitext(video_filename)[0]
        
        # 优先加载pickle格式
        pickle_path = os.path.join(self.metadata_dir, f"{base_name}.pkl")
        if os.path.exists(pickle_path):
            with open(pickle_path, 'rb') as f:
                return pickle.load(f)
                
        # 其次加载JSON格式
        json_path = os.path.join(self.metadata_dir, f"{base_name}.json")
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        return None
        
    def export_for_training(self, output_path, format='json'):
        """
        导出数据用于训练
        可以根据需要定制导出格式
        """
        all_metadata = []
        
        # 收集所有元数据
        for filename in os.listdir(self.metadata_dir):
            if filename.endswith('.json'):
                with open(os.path.join(self.metadata_dir, filename), 'r') as f:
                    metadata = json.load(f)
                    all_metadata.append(metadata)
                    
        # 根据格式导出
        if format == 'json':
            with open(output_path, 'w') as f:
                json.dump(all_metadata, f, indent=2)
        elif format == 'csv':
            # TODO: 实现CSV导出
            pass
        elif format == 'numpy':
            # TODO: 实现numpy数组导出
            pass
            
        return len(all_metadata) 