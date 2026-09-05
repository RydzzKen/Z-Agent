"""Task management tools (tasks.json)."""
import json
from datetime import datetime

from ..config import state
from ..ui import colors


def load_tasks():
    if os.path.exists(state.TASK_FILE):
        try:
            with open(state.TASK_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"tasks": [], "completed": []}


def save_tasks(data):
    try:
        with open(state.TASK_FILE, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False


def add_task(description):
    tasks = load_tasks()
    task_id = len(tasks["tasks"]) + len(tasks["completed"]) + 1
    tasks["tasks"].append({
        "id": task_id,
        "description": description,
        "created": datetime.now().isoformat()
    })
    if save_tasks(tasks):
        return f"✅ Task #{task_id} ditambahkan: {description}"
    return "❌ Gagal menyimpan task"


def list_tasks():
    tasks = load_tasks()
    if not tasks["tasks"] and not tasks["completed"]:
        return "📭 Tidak ada task"

    result = []
    if tasks["tasks"]:
        result.append("📋 **PENDING TASKS:**")
        for task in tasks["tasks"]:
            result.append(f"  [{task['id']}] {task['description']}")
    if tasks["completed"]:
        result.append("\n✅ **COMPLETED TASKS:**")
        for task in tasks["completed"][-5:]:  # 5 terakhir
            result.append(f"  [{task['id']}] {task['description']}")
    return "\n".join(result)


def complete_task(task_id):
    tasks = load_tasks()
    for i, task in enumerate(tasks["tasks"]):
        if task["id"] == task_id:
            task["completed_at"] = datetime.now().isoformat()
            tasks["completed"].append(task)
            tasks["tasks"].pop(i)
            save_tasks(tasks)
            return f"✅ Task #{task_id} selesai!"
    return "❌ Task tidak ditemukan"


def delete_task(task_id):
    tasks = load_tasks()
    for i, task in enumerate(tasks["tasks"]):
        if task["id"] == task_id:
            tasks["tasks"].pop(i)
            save_tasks(tasks)
            return f"✅ Task #{task_id} dihapus!"
    return "❌ Task tidak ditemukan"


import os  # noqa: E402
