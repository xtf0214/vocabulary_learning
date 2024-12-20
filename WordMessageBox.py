import datetime
from queue import PriorityQueue
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QKeySequence
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QComboBox,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QShortcut,
)
from utils import c2j, get_translation, j2c, load_dictionary


class WordMessageBox(QMessageBox):
    def __init__(self, main_window, word):
        super().__init__()
        self.main_window = main_window
        word_history = main_window.history["data"][word]
        # 设置标题和内容
        self.setWindowTitle(
            f"熟练度:{word_history['level']}"
            + f" 记忆次数:{word_history['count']}"
            + f" 正确率:{ word_history['correct'] / word_history['count'] * 100 if word_history['count'] > 0 else 0 :.0f}%"
        )
        self.setText(word)
        # 添加认识和忘记按钮
        self.setStandardButtons(WordMessageBox.Ok | WordMessageBox.Cancel)
        self.button(WordMessageBox.Ok).setText("认识(←)")
        self.button(WordMessageBox.Cancel).setText("忘记(→)")
        # 添加查看翻译的按钮
        self.translate_button = self.addButton("翻译(↑)", WordMessageBox.ActionRole)
        # 添加加入收藏夹的按钮
        self.favorite_button = self.addButton(
            "取消收藏(↓)" if word in main_window.favorite else "收藏(↓)", WordMessageBox.ActionRole
        )
        # 设置消息框始终置顶
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        # 设置字体大小
        font = QFont()
        font.setPointSize(18)
        font.setFamily("Microsoft YaHei")
        self.setFont(font)
        # 设置快捷键
        ok_shortcut = QShortcut(QKeySequence(Qt.Key_Left), self)
        cancel_shortcut = QShortcut(QKeySequence(Qt.Key_Right), self)
        translate_shortcut = QShortcut(QKeySequence(Qt.Key_Up), self)
        favorite_shortcut = QShortcut(QKeySequence(Qt.Key_Down), self)
        # 绑定快捷键到按钮的点击事件
        ok_shortcut.activated.connect(self.button(WordMessageBox.Ok).click)
        cancel_shortcut.activated.connect(self.button(WordMessageBox.Cancel).click)
        translate_shortcut.activated.connect(self.translate_button.click)
        favorite_shortcut.activated.connect(self.favorite_button.click)

    # 关闭窗口
    def closeEvent(self, event):
        print(f"{datetime.datetime.now()} Save and quit.")
        self.main_window.running = False
        self.close()
