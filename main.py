import datetime
import json
import os
import sys
import time
from queue import PriorityQueue
from PyQt5 import QtCore, QtGui, QtWidgets
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
import requests


class WordMessageBox(QMessageBox):
    def __init__(self, main_window, word):
        super().__init__()
        self.main_window = main_window

        word_history = main_window.history["data"][word]
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
        if word in main_window.favorite:
            self.favorite_button = self.addButton("取消收藏(↓)", WordMessageBox.ActionRole)
        else:
            self.favorite_button = self.addButton("收藏(↓)", WordMessageBox.ActionRole)
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.running = True
        self.queue = PriorityQueue()
        self.history = {"queue": [], "data": {}}
        self.favorite = []
        self.word_messagebox = None

    def initUI(self):
        # 设置窗口属性
        self.setWindowTitle("弹窗背单词")
        self.resize(400, 200)
        # 设置字体
        font = QFont()
        font.setPointSize(14)
        font.setFamily("Microsoft YaHei")
        self.setFont(font)

        # 创建主窗口的中心部件
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        # 创建主布局
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # 选择词库
        first_layout = QHBoxLayout()
        main_layout.addLayout(first_layout)
        choose_dict_labe = QLabel("选择词库：")
        choose_dict_labe.setFont(font)
        self.choose_dict = QComboBox()
        try:
            dict_list = [
                item.replace(".json", "")
                for item in os.listdir(os.path.join(os.getcwd(), "dicts"))
                if item.endswith(".json")
            ]
        except FileNotFoundError:
            dict_list = []
        if os.path.exists(os.path.join("./database/favorite.json")):
            dict_list = ["favorite"] + dict_list
        if os.path.exists(os.path.join("./database/history.json")):
            dict_list = ["history"] + dict_list
        for item in dict_list:
            self.choose_dict.addItem(item)
        first_layout.addWidget(choose_dict_labe)
        first_layout.addWidget(self.choose_dict)

        # 开始按钮
        self.start_button = QPushButton("开始")
        self.start_button.setFont(font)
        main_layout.addWidget(self.start_button)
        self.start_button.clicked.connect(self.start_review)

    def show_word(self, word):
        # 创建一个单词弹窗
        self.word_messagebox = WordMessageBox(self, word)
        # 显示单词弹窗并获取用户的选择
        result = self.word_messagebox.exec_()
        # 处理查看翻译按钮的点击事件
        if self.word_messagebox.clickedButton() == self.word_messagebox.translate_button:
            translation = self.get_translation(word)
            self.word_messagebox.setText(f"{word}\n{translation}")
            self.word_messagebox.translate_button.setDisabled(True)
            result = self.word_messagebox.exec_()
        # 处理加入/移除收藏夹的点击事件
        if self.word_messagebox.clickedButton() == self.word_messagebox.favorite_button:
            if word in self.favorite:
                self.favorite.remove(word)
                print(f"{datetime.datetime.now()} \033[0;34mUncollect\033[0m {word}.")
            else:
                self.favorite.append(word)
                print(f"{datetime.datetime.now()} \033[0;34mCollect\033[0m {word}.")
            self.word_messagebox.favorite_button.setDisabled(True)
            result = self.word_messagebox.exec_()
        # 根据用户的选择执行不同的操作
        if result == WordMessageBox.Ok:
            print(f"{datetime.datetime.now()} \033[0;32mRemembered\033[0m {word}.")
            return True
        elif result == WordMessageBox.Cancel:
            print(f"{datetime.datetime.now()} \033[0;31mForgot\033[0m {word}.")
            return False

    def alert(self, message):
        QMessageBox.information(self, "提示", message)

    def get_translation(self, word):
        url = f"https://dict.youdao.com/suggest?num=5&ver=3.0&doctype=json&cache=false&le=en&q={word}"
        try:
            res = requests.get(url).json()
            return res["data"]["entries"][0]["explain"]
        except:
            return "[网络连接失败或找不到该单词]"

    def load_data(self):
        # 读取历史记录
        try:
            with open("./database/history.json", "r", encoding="utf-8") as f:
                self.history = json.load(f)
        except FileNotFoundError:
            if not os.path.exists("./database"):
                os.mkdir("./database")
        # 读取收藏夹
        try:
            with open("./database/favorite.json", "r", encoding="utf-8") as f:
                self.favorite = json.load(f)
        except FileNotFoundError:
            if not os.path.exists("./database"):
                os.mkdir("./database")

    def start_review(self):
        self.running = True
        self.load_data()
        # 获取用户选择的复习时间间隔
        intervals = [0, 300, 1800, 10800, 43200, 86400, 172800, 345600, 604800, 1296000, 2592000]
        try:
            with open("./database/config.json", "r", encoding="utf-8") as f:
                intervals = json.load(f)["intervals"]
        except FileNotFoundError:
            with open("./database/config.json", "w", encoding="utf-8") as f:
                json.dump({"intervals": intervals}, f, indent=4)

        # 加载选择的词库
        src = self.choose_dict.currentText()
        if src == "":
            self.alert("请将词库放在 dicts 目录后后重试！")
            self.running = False
            self.save_data()
            return
        elif src == "history":
            for start_time, word, level in self.history["queue"]:
                self.queue.put((start_time, word, level))
            self.history["queue"] = []
        elif src == "favorite":
            for word in self.favorite:
                if word in self.history["data"]:
                    level = self.history["data"][word]["level"]
                    if level < len(intervals):
                        self.queue.put((self.history["data"][word]["records"][-1][0] + intervals[level], word, level))
                else:
                    level = 0
                    self.history["data"][word] = {"level": 0, "correct": 0, "count": 0, "records": []}
                    self.queue.put((time.time() + intervals[level], word, level))
        else:
            words = json.load(open(f"./dicts/{src}.json", "r", encoding="utf-8"))
            for word in words:
                if word in self.history["data"]:
                    level = self.history["data"][word]["level"]
                    if level < len(intervals):
                        self.queue.put((self.history["data"][word]["records"][-1][0] + intervals[level], word, level))
                else:
                    level = 0
                    self.history["data"][word] = {"level": 0, "correct": 0, "count": 0, "records": []}
                    self.queue.put((time.time() + intervals[level], word, level))
        # 执行背单词
        cnt = 0
        while not self.queue.empty() and self.running:
            start_time, word, level = self.queue.queue[0]
            if time.time() >= start_time:
                correct = self.show_word(word)
                # 如果没有关闭单词弹窗
                if self.running:
                    self.queue.get()
                    cur_time = time.time()
                    self.history["data"][word]["count"] += 1
                    level = level + 1 if correct else 0
                    self.history["data"][word]["records"].append((cur_time, correct))
                    self.history["data"][word]["level"] = level
                    if level < len(intervals):
                        self.queue.put((cur_time + intervals[level], word, level))
            # 每分钟保存一次数据
            if self.running:
                time.sleep(1)
                cnt = (cnt + 1) % 60
                if cnt == 0:
                    self.save_data()

        if self.running:
            self.running = False
            self.save_data()
            self.alert("所有单词已背完！")
        else:
            self.save_data()
            self.alert("数据已保存！")

    def save_data(self):
        self.history["queue"] = self.queue.queue
        with open("./database/history.json", "w") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=4)
        with open("./database/favorite.json", "w") as f:
            json.dump(self.favorite, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
