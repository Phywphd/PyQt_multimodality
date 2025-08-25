"""
摄像头录制应用主入口
"""
import sys
from PyQt5.QtWidgets import QApplication
from frontend.main_window import MainWindow


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("视频数据记录系统")
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec_())


if __name__ == '__main__':
    main() 