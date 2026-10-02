import json
import subprocess
import sys

data = json.load(sys.stdin)
if data.get("stop_hook_active"):
    sys.exit(0)   # already blocked once this turn: don't loop forever

r = subprocess.run(["uv", "run", "pytest", "-q", "-x"], capture_output=True, text=True)
if r.returncode != 0:
    print("Tests are failing. Fix them before finishing:\n" + r.stdout[-3000:], file=sys.stderr)
    sys.exit(2)
sys.exit(0)