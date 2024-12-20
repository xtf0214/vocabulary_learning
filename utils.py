import ast
import csv
import os
import sys
import requests
from bs4 import BeautifulSoup


def get_translation(word):
    url = f"https://dict.youdao.com/result?word={word}&lang=en"
    try:
        response = requests.get(url)
        bs = BeautifulSoup(response.content, "lxml")
        rt = bs.find("section")
        phonetic_symbol = rt.find("div", attrs={"class": "phone_con"}).text
        translation = [item.text for item in rt.find("div", attrs={"class": "dict-book"}).find_all("li")]
        return phonetic_symbol + "\n" + "\n".join(translation)
    except:
        return "[网络连接失败或找不到该单词]"


def load_dictionary():
    dict_list = []
    if os.path.exists("./database/history.json"):
        dict_list.append("history")
    if os.path.exists("./database/favorite.json"):
        dict_list.append("favorite")
    if os.path.exists("./dicts"):
        for item in os.listdir(os.path.join(os.getcwd(), "dicts")):
            if item.endswith(".json"):
                dict_list.append(item.replace(".json", ""))
    return dict_list

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
        print(os.path.abspath("."))
    return os.path.join(base_path, relative_path)

def c2j(tables: list[list]):
    tables = list(tables)
    dicts = {}
    for item in tables[1:]:
        key = item[0]
        dicts[key] = {tables[0][i]: ast.literal_eval(item[i]) for i in range(1, len(item))}
    return dicts


def j2c(dicts: dict):
    dicts = list(dicts.items())
    if not dicts:
        return []
    tables = []
    tables.append(["key"] + list(dicts[0][1].keys()))
    for k, d in dicts:
        tables.append([k] + list(d.values()))
    return tables


if __name__ == "__main__":
    # print(get_translation("hello"))
    # print(load_dictionary())

    data = {"vehicle": {"level": 1, "correct": 0, "count": 1, "records": [[1734597765.4355662, True]]}}

    with open("./queue.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        for item in j2c(data):
            writer.writerow(item)

    # 打开CSV文件
    with open("./queue.csv", mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        print(c2j(list(reader)))
