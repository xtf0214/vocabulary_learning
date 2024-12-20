import csv
import datetime
import json
import os
import sys
import time
from queue import PriorityQueue
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QKeySequence, QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from utils import c2j, get_translation, j2c, load_dictionary, resource_path
from WordMessageBox import WordMessageBox
from MainWindow_ui import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.initUI()

        self.intervals = [0, 300, 1800, 10800, 43200, 86400, 172800, 345600, 604800, 1296000, 2592000]
        if not os.path.exists("./database"):
            os.mkdir("./database")
        if os.path.exists("./database/config.json"):
            with open("./database/config.json", "r", encoding="utf-8") as f:
                self.intervals = json.load(f)["intervals"]
        else:
            with open("./database/config.json", "w", encoding="utf-8") as f:
                json.dump({"intervals": self.intervals}, f, ensure_ascii=False, indent=4)
        self.full_level = len(self.intervals)
        self.running = True
        self.ready_queue = [PriorityQueue() for _ in range(self.full_level)]
        self.history = {"queue": [[] for _ in range(self.full_level)], "data": {}}
        self.favorite = []
        self.word_messagebox = None

    def initUI(self):
        # 设置字体
        font = self.font()
        font.setPointSize(14)
        font.setFamily("Microsoft YaHei")
        self.setFont(font)
        # 设置窗口图标
        self.setWindowIcon(QIcon(resource_path("./static/icon.png")))
        # 动态加载词库
        for item in load_dictionary():
            self.choose_dict.addItem(item)
        self.start_button.clicked.connect(self.start)
        self.search_button.clicked.connect(self.search_word)

    def show_word(self, word):
        # 创建一个单词弹窗
        self.word_messagebox = WordMessageBox(self, word)
        # 显示单词弹窗并获取用户的选择
        result = self.word_messagebox.exec_()
        # 处理查看翻译按钮的点击事件
        if self.word_messagebox.clickedButton() == self.word_messagebox.translate_button:
            translation = get_translation(word)
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

    def search_word(self, word):
        word = self.word_input.text().strip()
        translation = get_translation(word)
        self.alert(word + "\n" + translation)

    def load_data(self):
        # 读取历史记录和收藏夹数据
        if os.path.exists("./database/history.json"):
            with open("./database/history.json", "r", encoding="utf-8") as file:
                self.history = json.load(file)
        queue = [[item[1] for item in q] for q in self.history["queue"]]
        for i in range(len(queue)):
            print(i, queue[i])
        if os.path.exists("./database/favorite.json"):
            with open("./database/favorite.json", "r", encoding="utf-8") as file:
                self.favorite = json.load(file)

    def start(self):
        self.running = True
        self.load_data()
        # 加载选择的词库
        src = self.choose_dict.currentText()
        if src == "":
            self.alert("请将词库放在 dicts 目录后后重试！")
            self.running = False
            self.save_data()
            return
        elif src == "history":
            for level in range(self.full_level):
                for start_time, word in self.history["queue"][level]:
                    self.ready_queue[level].put((start_time, word))
            self.history["queue"] = [[] for _ in range(self.full_level)]
        else:
            if src == "favorite":
                words = self.favorite
            else:
                words = json.load(open(f"./dicts/{src}.json", "r", encoding="utf-8"))
            for word in words:
                if word in self.history["data"] and self.history["data"][word]["count"] > 0:
                    level = self.history["data"][word]["level"]
                    if level < self.full_level:
                        self.ready_queue[level].put(
                            (self.history["data"][word]["records"][-1][0] + self.intervals[level], word)
                        )
                else:
                    level = 0
                    self.history["data"][word] = {"level": 0, "correct": 0, "count": 0, "records": []}
                    self.ready_queue[level].put((time.time() + self.intervals[level], word))

        # 执行背单词
        cnt = 0
        while any(not q.empty() for q in self.ready_queue) and self.running:
            for level in range(len(self.ready_queue) - 1, -1, -1):
                if self.ready_queue[level].empty():
                    continue
                start_time, word = self.ready_queue[level].queue[0]
                if time.time() >= start_time:
                    correct = self.show_word(word)
                    # 如果没有关闭单词弹窗
                    if self.running:
                        self.ready_queue[level].get()
                        cur_time = time.time()
                        self.history["data"][word]["count"] += 1
                        self.history["data"][word]["correct"] += 1 if correct else 0
                        self.history["data"][word]["records"].append((cur_time, correct))
                        level = level + 1 if correct else 0
                        self.history["data"][word]["level"] = level
                        if level < len(self.ready_queue):
                            self.ready_queue[level].put((cur_time + self.intervals[level], word))
                    break
            # 每分钟保存一次数据
            if self.running:
                time.sleep(1)
                cnt = (cnt + 1) % 10
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
        self.history["queue"] = [self.ready_queue[i].queue for i in range(self.full_level)]
        self.ready_queue = [PriorityQueue() for _ in range(self.full_level)]
        with open("./database/history.json", "w") as file:
            json.dump(self.history, file, ensure_ascii=False, indent=4)
        with open("./database/favorite.json", "w") as file:
            json.dump(self.favorite, file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
