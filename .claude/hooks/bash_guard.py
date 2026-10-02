import json
import re
import sys

data = json.load(sys.stdin)
tool_input = data.get("tool_input", {})
cmd = tool_input.get("command", "")

def decide(decision, reason, updated=None):
    out = {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": reason,
    }}
    if updated is not None:
        out["hookSpecificOutput"]["updatedInput"] = updated
    print(json.dumps(out))
    sys.exit(0)

if re.search(r"git\s+push\b.*\b(main|master)\b", cmd) or "--force" in cmd:
    decide("deny", "Pushing to main or force-pushing is blocked. Push a feature branch and open a PR.")

if re.search(r"cal_live_\w+", cmd):
    new_input = dict(tool_input)   # keep every other field unchanged
    new_input["command"] = re.sub(r"cal_live_\w+", "$CALENDAR_API_KEY", cmd)
    decide("allow", "Replaced a live calendar key with the environment variable.", new_input)

sys.exit(0)