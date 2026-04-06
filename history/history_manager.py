# history_manager.py
import os
import json
from datetime import datetime

def save_snapshot(report, history_folder="reports/history"):
    """
    Save a timestamped snapshot of the report in the history folder.
    """
    if not os.path.exists(history_folder):
        os.makedirs(history_folder)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(history_folder, f"{timestamp}.json")

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"🗂 Snapshot saved: {filename}")


def load_snapshots(history_folder="reports/history"):
    """
    Load all historical snapshots from the history folder.
    Returns a list of reports.
    """
    if not os.path.exists(history_folder):
        return []

    files = sorted(os.listdir(history_folder))
    snapshots = []
    for file in files:
        with open(os.path.join(history_folder, file), "r", encoding="utf-8") as f:
            snapshots.append(json.load(f))
    return snapshots