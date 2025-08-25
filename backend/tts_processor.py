"""
语音合成处理器 - 文本转语音输出模块
"""
import pyttsx3
from PyQt5.QtCore import QObject, QThread, pyqtSignal
import sys


class TTSWorker(QThread):
    """TTS工作线程"""
    speech_started = pyqtSignal()
    speech_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.text_to_speak = ""
        self.tts_engine = None
        self.voice_rate = 150
        self.voice_volume = 0.9
        self.voice_id = 0  # 0为男声，1为女声(如果可用)
        
    def init_engine(self):
        """初始化TTS引擎"""
        try:
            self.tts_engine = pyttsx3.init()
            
            # 设置语音属性
            self.tts_engine.setProperty('rate', self.voice_rate)
            self.tts_engine.setProperty('volume', self.voice_volume)
            
            # 获取可用语音
            voices = self.tts_engine.getProperty('voices')
            if voices and len(voices) > self.voice_id:
                self.tts_engine.setProperty('voice', voices[self.voice_id].id)
                
        except Exception as e:
            self.error_occurred.emit(f"TTS引擎初始化失败: {str(e)}")
            
    def set_text(self, text):
        """设置要朗读的文本"""
        self.text_to_speak = text
        
    def set_voice_properties(self, rate=150, volume=0.9, voice_id=0):
        """设置语音属性"""
        self.voice_rate = rate
        self.voice_volume = volume
        self.voice_id = voice_id
    
    def run(self):
        """执行语音合成"""
        try:
            if not self.tts_engine:
                self.init_engine()
                
            if not self.tts_engine:
                return
                
            if self.text_to_speak:
                self.speech_started.emit()
                self.tts_engine.say(self.text_to_speak)
                self.tts_engine.runAndWait()
                self.speech_finished.emit()
                
        except Exception as e:
            self.error_occurred.emit(f"语音合成错误: {str(e)}")


class TTSProcessor(QObject):
    """语音合成处理器主类"""
    
    speech_started = pyqtSignal()
    speech_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self.is_speaking = False
        
        # 默认语音设置
        self.voice_settings = {
            'rate': 150,      # 语音速度 (100-300)
            'volume': 0.9,    # 音量 (0.0-1.0)
            'voice_id': 0     # 语音ID
        }
        
    def speak(self, text):
        """朗读文本"""
        if not text or not text.strip():
            return
            
        # 停止当前朗读
        self.stop_speaking()
        
        # 创建新的工作线程
        self.worker = TTSWorker()
        self.worker.speech_started.connect(self._on_speech_started)
        self.worker.speech_finished.connect(self._on_speech_finished)
        self.worker.error_occurred.connect(self.error_occurred.emit)
        
        # 设置语音属性
        self.worker.set_voice_properties(
            self.voice_settings['rate'],
            self.voice_settings['volume'],
            self.voice_settings['voice_id']
        )
        
        # 设置文本并开始朗读
        self.worker.set_text(text)
        self.worker.start()
    
    def stop_speaking(self):
        """停止朗读"""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            self.is_speaking = False
    
    def set_voice_rate(self, rate):
        """设置语音速度"""
        self.voice_settings['rate'] = max(50, min(300, rate))
    
    def set_voice_volume(self, volume):
        """设置音量"""
        self.voice_settings['volume'] = max(0.0, min(1.0, volume))
    
    def set_voice_gender(self, voice_id):
        """设置语音性别"""
        self.voice_settings['voice_id'] = voice_id
    
    def get_voice_settings(self):
        """获取当前语音设置"""
        return self.voice_settings.copy()
    
    def is_busy(self):
        """检查是否正在朗读"""
        return self.is_speaking
    
    def _on_speech_started(self):
        """朗读开始回调"""
        self.is_speaking = True
        self.speech_started.emit()
    
    def _on_speech_finished(self):
        """朗读完成回调"""
        self.is_speaking = False
        self.speech_finished.emit()
    
    @staticmethod
    def get_available_voices():
        """获取可用的语音列表"""
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            voice_list = []
            
            for i, voice in enumerate(voices):
                voice_info = {
                    'id': i,
                    'name': voice.name if hasattr(voice, 'name') else f"Voice {i}",
                    'language': voice.languages if hasattr(voice, 'languages') else 'Unknown'
                }
                voice_list.append(voice_info)
                
            engine.stop()
            return voice_list
            
        except Exception as e:
            print(f"获取语音列表失败: {e}")
            return [{'id': 0, 'name': 'Default Voice', 'language': 'Unknown'}]