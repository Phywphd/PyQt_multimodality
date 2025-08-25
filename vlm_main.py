"""
VLM多模态演示系统主入口 - 集成Qwen2.5-VL + 语音输出
"""
import sys
from PyQt5.QtWidgets import QApplication
from frontend.vlm_main_window import VLMMainWindow


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("VLM多模态演示系统")
    app.setApplicationDisplayName("摄像头/视频 + Qwen2.5-VL + 语音输出")
    
    # 创建主窗口
    window = VLMMainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()