#!/usr/bin/env python3
import sys
import os
import re

def main():
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python task_brief.py PLAN_FILE TASK_NUMBER [OUTFILE]")
        sys.exit(2)

    plan_file = sys.argv[1]
    task_num = sys.argv[2]

    if not os.path.isfile(plan_file):
        print(f"Error: no such plan file: {plan_file}", file=sys.stderr)
        sys.exit(2)

    # Resolve output file path
    if len(sys.argv) == 4:
        out_file = sys.argv[3]
    else:
        # Default output directory: .agents/sdd/ relative to workspace root
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        sdd_dir = os.path.join(repo_root, ".agents", "sdd")
        os.makedirs(sdd_dir, exist_ok=True)
        out_file = os.path.join(sdd_dir, f"task-{task_num}-brief.md")

    with open(plan_file, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.splitlines()
    in_fence = False
    in_task = False
    task_lines = []

    # Match header pattern like: "# Task 1: Setup" or "## Task 2"
    task_pattern = re.compile(rf"^#+\s+Task\s+{task_num}(\b|[^0-9])", re.IGNORECASE)
    any_task_pattern = re.compile(r"^#+\s+Task\s+[0-9]+", re.IGNORECASE)

    for line in lines:
        if line.strip().startswith("```"):
            in_fence = not in_fence
        
        if not in_fence:
            if task_pattern.match(line):
                in_task = True
            elif any_task_pattern.match(line) and in_task:
                # Found another task header, stop collecting
                break
        
        if in_task:
            task_lines.append(line)

    if not task_lines:
        print(f"Error: Task {task_num} not found in {plan_file} (no heading matching 'Task {task_num}')", file=sys.stderr)
        sys.exit(3)

    with open(out_file, "w", encoding="utf-8") as f:
        f.write("\n".join(task_lines) + "\n")

    print(f"Wrote {out_file}: {len(task_lines)} lines")

if __name__ == "__main__":
    main()
