import json
from prettytable import PrettyTable

from utils import j2c

with open("./database/history.json", "r", encoding="utf-8") as file:
    history = json.load(file)
    queue = [[item[1] for item in q] for q in history["queue"]]
    for i in range(len(queue)):
        print(i + 1, queue[i])
    records = j2c(history["data"])
    records_table = PrettyTable(records[0])
    for record in records[1:]:
        records_table.add_row(record)
    # print(records_table)
