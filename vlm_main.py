"""
VLM多模态演示系统主入口 - 集成Qwen2.5-VL + 语音输出
"""
import sys
import os

# 设置Qt插件路径
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = '/home/hyp/miniconda3/envs/qwen_vlm/lib/python3.9/site-packages/PyQt5/Qt5/plugins/platforms'

# 设置输入法环境变量 - 优先使用系统默认
if 'QT_IM_MODULE' not in os.environ:
    # 尝试不同的输入法模块
    for im_module in ['xim', 'compose']:
        os.environ['QT_IM_MODULE'] = im_module
        break
os.environ['LANG'] = 'zh_CN.UTF-8'
os.environ['LC_CTYPE'] = 'zh_CN.UTF-8'

from PyQt5.QtWidgets import QApplication
from frontend.vlm_main_window import VLMMainWindow


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("VLM多模态演示系统")
    app.setApplicationDisplayName("摄像头/视频 + Qwen2.5-VL + 语音输出")
    
    # 设置中文支持
    import locale
    try:
        locale.setlocale(locale.LC_ALL, '')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
        except:
            pass
    
    # 确保中文输入法支持
    from PyQt5.QtCore import Qt
    try:
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        # 强制启用输入法支持
        app.setAttribute(Qt.AA_Use96Dpi, False)
        app.setAttribute(Qt.AA_DontShowIconsInMenus, False)
    except:
        pass
    
    # 设置输入法模式
    try:
        app.setInputMethod(None)  # 使用系统默认输入法
    except:
        pass
    
    # 设置中文字体
    from PyQt5.QtGui import QFont
    font = QFont()
    font.setFamily("Noto Sans CJK SC")  # 使用安装的中文字体
    if not font.exactMatch():
        font.setFamily("WenQuanYi Zen Hei")  # 备选字体
    if not font.exactMatch():
        font.setFamily("WenQuanYi Micro Hei")  # 第二备选
    font.setPointSize(10)
    app.setFont(font)
    
    # 创建主窗口
    window = VLMMainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()