"""
git_tool.py - Local Git version control manager using Dulwich (Pure Python Git).
Provides standard git init, add, commit, status, and log operations.
"""
import sys
import os
import dulwich.porcelain as git
from dulwich.repo import Repo

def init_repo():
    """Initializes a local git repository if not already initialized."""
    if not os.path.exists(".git"):
        repo = git.init(".")
        print("[Git] Initialized empty Git repository in .git/")
    else:
        repo = Repo(".")
        print("[Git] Using existing Git repository in .git/")
    return repo

def add_all():
    """Stages all files (except .git) in the repository."""
    init_repo()
    # Find all files
    all_files = []
    for root, dirs, files in os.walk("."):
        if ".git" in dirs:
            dirs.remove(".git")
        if "__pycache__" in dirs:
            dirs.remove("__pycache__")
        if "build" in dirs:
            dirs.remove("build")
        if "dist" in dirs:
            dirs.remove("dist")
        for f in files:
            rel_path = os.path.relpath(os.path.join(root, f), ".").replace("\\", "/")
            all_files.append(rel_path)

    git.add(".", paths=all_files)
    print(f"[Git] Staged {len(all_files)} files.")

def commit(message="Update codebase and bugfixes"):
    """Commits staged changes."""
    add_all()
    try:
        commit_id = git.commit(".", message=message.encode('utf-8'), author=b"Developer <developer@bubblearena.local>")
        commit_hex = commit_id.decode('ascii') if isinstance(commit_id, bytes) else str(commit_id)
        print(f"[Git] Committed [{commit_hex[:7]}]: {message}")
    except Exception as e:
        print(f"[Git] Commit status: {e}")

def log():
    """Shows git commit history."""
    try:
        git.log(".", max_entries=5)
    except Exception as e:
        print(f"[Git] Log error: {e}")

def status():
    """Shows repository status."""
    try:
        st = git.status(".")
        print("[Git] Staged:", st.staged)
        print("[Git] Untracked:", st.untracked)
    except Exception as e:
        print(f"[Git] Status: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "init":
            init_repo()
        elif cmd == "add":
            add_all()
        elif cmd == "commit":
            msg = sys.argv[2] if len(sys.argv) > 2 else "Update"
            commit(msg)
        elif cmd == "log":
            log()
        elif cmd == "status":
            status()
        else:
            print(f"Unknown command: {cmd}")
    else:
        add_all()
        commit("Initial commit: 4-Player Retro 2D Arcade Brawler in Python Pygame")
