#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门的中文输入组件 - 支持中文输入的QLineEdit
"""

from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class ChineseInputLineEdit(QLineEdit):
    """支持中文输入的QLineEdit"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_chinese_support()
        
    def setup_chinese_support(self):
        """设置中文输入支持"""
        # 设置字体
        font = QFont()
        font_families = ["Noto Sans CJK SC", "WenQuanYi Zen Hei", "WenQuanYi Micro Hei", "SimHei", "Microsoft YaHei"]
        for font_family in font_families:
            font.setFamily(font_family)
            if font.exactMatch():
                break
        font.setPointSize(12)
        self.setFont(font)
        
        # 设置输入法属性
        self.setAttribute(Qt.WA_InputMethodEnabled, True)
        self.setInputMethodHints(Qt.ImhNone)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAttribute(Qt.WA_KeyCompression, False)
    
    def focusInEvent(self, event):
        """获得焦点时重新激活输入法"""
        super().focusInEvent(event)
        # 重新激活输入法
        self.setAttribute(Qt.WA_InputMethodEnabled, True)
        self.setInputMethodHints(Qt.ImhNone)
        self.setFocus(Qt.OtherFocusReason)