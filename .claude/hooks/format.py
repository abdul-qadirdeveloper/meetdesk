import json
import subprocess
import sys

data = json.load(sys.stdin)
path = data.get("tool_input", {}).get("file_path", "")

if path.endswith(".py"):
    subprocess.run(["uv", "run", "ruff", "format", path], capture_output=True)
    r = subprocess.run(["uv", "run", "ruff", "check", "--fix", path],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f"ruff found problems in {path}:\n{r.stdout}", file=sys.stderr)
        sys.exit(2)   # blocking: stderr goes back to Claude
sys.exit(0)