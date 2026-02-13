import json
import os

# Find the most recently modified session file
memory_dir = "app/services/ai/conversation_memory"
files = []
for f in os.listdir(memory_dir):
    if f.endswith('.json'):
        path = os.path.join(memory_dir, f)
        files.append((os.path.getmtime(path), path, f))

files.sort(reverse=True)

for mtime, path, name in files[:3]:
    print(f"\n=== {name} ===")
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    
    print(f"  last_query: {data.get('last_query')!r}")
    print(f"  product_type: {data.get('product_type')!r}")
    print(f"  history_len: {len(data.get('history', []))}")
    
    hist = data.get("history", [])
    for m in hist[-4:]:
        content = m.get("content", "")[:100]
        print(f"  [{m.get('role')}]: {content}")
