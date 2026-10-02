---
name: verify-change
description: Always use before saying a task is complete. Use after implementing, refactoring or fixing anything in src/ or tests/.
---
# Verify a change

1. Run `bash check.sh` from this skill's own directory (the folder containing this SKILL.md) and capture the output.
2. Read `git diff` for the change.
3. Confirm no test was weakened: no deleted asserts, no loosened comparisons,
   no changed expected values, no new skips. See reference.md for examples.
4. Report PASS or FAIL with the evidence: each gate's result and any suspicious
   diff hunks with file:line.

Never report PASS without having run step 1 in this turn.