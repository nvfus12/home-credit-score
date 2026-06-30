#!/usr/bin/env python3
import sys
import os
import subprocess

def run_git(args):
    try:
        res = subprocess.run(
            ["git"] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Git error running {' '.join(args)}: {e.stderr.strip()}", file=sys.stderr)
        sys.exit(2)

def main():
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python review_package.py BASE HEAD [OUTFILE]")
        sys.exit(2)

    base = sys.argv[1]
    head = sys.argv[2]

    # Verify commits
    run_git(["rev-parse", "--verify", base])
    run_git(["rev-parse", "--verify", head])

    base_short = run_git(["rev-parse", "--short", base])
    head_short = run_git(["rev-parse", "--short", head])

    if len(sys.argv) == 4:
        out_file = sys.argv[3]
    else:
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        sdd_dir = os.path.join(repo_root, ".agents", "sdd")
        os.makedirs(sdd_dir, exist_ok=True)
        out_file = os.path.join(sdd_dir, f"review-{base_short}..{head_short}.diff")

    # Fetch stats
    commits = run_git(["log", "--oneline", f"{base}..{head}"])
    files_changed = run_git(["diff", "--stat", f"{base}..{head}"])
    diff_content = run_git(["diff", "-U10", f"{base}..{head}"])

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(f"# Review Package: {base}..{head}\n\n")
        f.write("## Commits\n")
        f.write("```text\n")
        f.write(commits + "\n")
        f.write("```\n\n")
        f.write("## Files Changed\n")
        f.write("```text\n")
        f.write(files_changed + "\n")
        f.write("```\n\n")
        f.write("## Diff\n")
        f.write("```diff\n")
        f.write(diff_content + "\n")
        f.write("```\n")

    print(f"Wrote {out_file}: {len(commits.splitlines())} commit(s)")

if __name__ == "__main__":
    main()
