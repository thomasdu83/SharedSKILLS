import json
import sys

for i in range(200):
    print(f"log {i}", file=sys.stderr, flush=True)

sys.stdout.write(json.dumps({"written": ["x" * 1000 for _ in range(200)]}))
sys.stdout.flush()