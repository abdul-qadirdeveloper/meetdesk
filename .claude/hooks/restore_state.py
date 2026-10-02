import subprocess

def run(*args):
    return subprocess.run(list(args), capture_output=True, text=True).stdout

print("State after compaction.")
print("Branch:", run("git", "branch", "--show-current").strip())
print("Changed vs main:\n" + run("git", "diff", "--stat", "main...HEAD"))
print("Uncommitted:\n" + run("git", "status", "--short"))