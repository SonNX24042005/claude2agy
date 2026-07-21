import os
import glob
import json
import sqlite3

def test_strict_claude(target_cwd):
    sanitized = "-" + os.path.abspath(target_cwd).strip("/").replace("/", "-")
    projects_dir = os.path.expanduser("~/.claude/projects")
    
    target_folder = os.path.join(projects_dir, sanitized)
    if os.path.exists(target_folder):
        files = glob.glob(os.path.join(target_folder, "*.jsonl"))
        print(f"Exact Claude project match '{sanitized}': {len(files)} files found.")
        return files
    else:
        print(f"Exact Claude project match '{sanitized}' not found directly.")
        matching_dirs = []
        if os.path.exists(projects_dir):
            for d in os.listdir(projects_dir):
                if d == sanitized:
                    matching_dirs.append(os.path.join(projects_dir, d))
        files = []
        for md in matching_dirs:
            files.extend(glob.glob(os.path.join(md, "*.jsonl")))
        print(f"Matched {len(files)} files strictly for project.")
        return files

def test_strict_agy(target_cwd):
    abs_cwd = os.path.abspath(target_cwd)
    summary_db = os.path.expanduser("~/.gemini/antigravity-cli/conversation_summaries.db")
    if not os.path.exists(summary_db):
        print("summary_db not found")
        return []
    conn = sqlite3.connect(summary_db)
    cursor = conn.cursor()
    
    cursor.execute("SELECT conversation_id, preview, last_modified_time, workspace_uris FROM conversation_summaries WHERE workspace_uris LIKE ? ORDER BY last_modified_time DESC", (f"%{abs_cwd}%",))
    rows = cursor.fetchall()
    conn.close()
    
    print(f"Strict AGY project match for '{abs_cwd}': {len(rows)} sessions found.")
    for r in rows[:5]:
        print("  -", r[0][:8], "|", r[1][:50])
    return rows

print("--- TESTING STRICT PROJECT FILTERING ---")
cwd1 = "/mnt/181EC3061EC2DBBE/DT/Code/kiaisoft/auto-design-ai-raw/auto-design-ai"
print(f"\n[Project: {cwd1}]")
test_strict_claude(cwd1)
test_strict_agy(cwd1)

cwd2 = "/mnt/181EC3061EC2DBBE/DT/Code/moon-asterisk/NB-Compass"
print(f"\n[Project: {cwd2}]")
test_strict_claude(cwd2)
test_strict_agy(cwd2)
