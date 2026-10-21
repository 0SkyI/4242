# -*- coding: utf-8 -*-
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def get_variant():
    path = ROOT / "src/variant.txt"
    if not path.exists():
        raise SystemExit("Не найден файл src/variant.txt.")
    letter = path.read_text(encoding="utf-8").strip().upper()[:1]
    if not (ROOT / "datasets" / letter).exists():
        raise SystemExit(f"Папки для варианта {letter!r} нет в datasets.")
    return letter

LOG = ROOT / "datasets" / get_variant() / "logs/agent.jsonl"

def clean(obj):
    if isinstance(obj, dict):
        return {k.strip(): clean(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean(x) for x in obj]
    if isinstance(obj, str):
        return obj.strip()
    return obj

entries = []
with LOG.open(encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            entries.append(clean(json.loads(line)))

creator = {}
for e in entries:
    if e.get("tool") == "create_order":
        res = e.get("result", {})
        if res.get("ok"):
            oid = res.get("data", {}).get("order_id")
            uid = e.get("args", {}).get("user_id")
            if oid and uid:
                creator[oid] = uid

first_suspicious = None
cancelled = []
for e in entries:
    if e.get("tool") == "cancel_order":
        if first_suspicious is None:
            first_suspicious = e.get("time")
        oid = e.get("args", {}).get("order_id")
        if oid:
            cancelled.append(oid)

cancel_started = False
beneficiary = None
benef_count = 0
for e in entries:
    tool = e.get("tool")
    if tool == "cancel_order":
        cancel_started = True
    elif tool == "create_order" and cancel_started:
        res = e.get("result", {})
        if res.get("ok"):
            uid = e.get("args", {}).get("user_id")
            if uid:
                if beneficiary is None:
                    beneficiary = uid
                    benef_count = 1
                elif uid == beneficiary:
                    benef_count += 1

others = sum(1 for oid in cancelled if creator.get(oid) != beneficiary)

# Выводим строго в требуемом формате, без лишних символов
print(f"первый подозрительный вызов: {first_suspicious}")
print(f"отменено чужих заказов: {others}")
print(f"аккаунт выгодоприобретателя: {beneficiary}")
print(f"оформлено на этот аккаунт: {benef_count}")