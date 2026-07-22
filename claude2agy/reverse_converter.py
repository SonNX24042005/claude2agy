import os
import json
import uuid
import sqlite3
from datetime import datetime

class AgyToClaudeConverter:
    def __init__(self, session_id=None, target_cwd=None):
        self.target_cwd = os.path.abspath(target_cwd or os.getcwd())
        self.session_id = session_id
        self.brain_dir = os.path.expanduser("~/.gemini/antigravity-cli/brain")

    @staticmethod
    def get_agy_sessions(target_cwd=None):
        """List ONLY Antigravity sessions strictly belonging to the target project directory."""
        target_cwd = os.path.abspath(target_cwd or os.getcwd())
        summary_db = os.path.expanduser("~/.gemini/antigravity-cli/conversation_summaries.db")
        sessions = []

        if os.path.exists(summary_db):
            try:
                conn = sqlite3.connect(summary_db)
                cursor = conn.cursor()
                # Strict filter by workspace_uris matching target_cwd
                cursor.execute(
                    "SELECT conversation_id, preview, last_modified_time FROM conversation_summaries WHERE workspace_uris LIKE ? ORDER BY last_modified_time DESC",
                    (f"%{target_cwd}%",)
                )
                rows = cursor.fetchall()
                conn.close()

                for row in rows:
                    sid, preview, mtime = row
                    sessions.append({
                        "id": sid,
                        "preview": preview if preview else "Antigravity Session",
                        "mtime": str(mtime)[:16]
                    })
            except Exception:
                pass

        return sessions

    def convert(self):
        """Convert AGY session transcript into a valid Claude Code .jsonl session."""
        if not self.session_id:
            raise ValueError("Session ID is required for reverse conversion!")

        transcript_path = os.path.join(self.brain_dir, self.session_id, ".system_generated", "logs", "transcript.jsonl")
        if not os.path.exists(transcript_path):
            raise FileNotFoundError(f"Antigravity transcript not found: {transcript_path}")

        print(f"📖 Reading Antigravity session transcript: {transcript_path}")

        records = []
        parent_uuid = None
        now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")

        # Create sanitized project folder name for ~/.claude/projects/
        sanitized_folder = "-" + self.target_cwd.strip("/").replace("/", "-")
        claude_project_dir = os.path.expanduser(f"~/.claude/projects/{sanitized_folder}")
        os.makedirs(claude_project_dir, exist_ok=True)

        target_claude_jsonl = os.path.join(claude_project_dir, f"{self.session_id}.jsonl")

        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    step = json.loads(line)
                    stype = step.get("type")
                    content = step.get("content", "")
                    created_at = step.get("created_at", now_iso)

                    if stype == "USER_INPUT":
                        clean_text = content
                        if "<USER_REQUEST>" in clean_text:
                            clean_text = clean_text.split("<USER_REQUEST>")[1].split("</USER_REQUEST>")[0].strip()

                        if "<IMPORTED_CONVERSATION_HISTORY>" in clean_text or "Initializing imported session history." in clean_text:
                            continue

                        cur_uuid = str(uuid.uuid4())
                        record = {
                            "parentUuid": parent_uuid,
                            "isSidechain": False,
                            "promptId": str(uuid.uuid4()),
                            "type": "user",
                            "message": {
                                "role": "user",
                                "content": [{"type": "text", "text": clean_text}]
                            },
                            "uuid": cur_uuid,
                            "timestamp": created_at,
                            "userType": "external",
                            "entrypoint": "claude-vscode",
                            "cwd": self.target_cwd,
                            "sessionId": self.session_id,
                            "version": "2.1.215",
                            "gitBranch": "dev"
                        }
                        records.append(record)
                        parent_uuid = cur_uuid

                    elif stype == "PLANNER_RESPONSE":
                        if content and content != "No response requested.":
                            cur_uuid = str(uuid.uuid4())
                            record = {
                                "parentUuid": parent_uuid,
                                "isSidechain": False,
                                "type": "assistant",
                                "uuid": cur_uuid,
                                "timestamp": created_at,
                                "message": {
                                    "id": str(uuid.uuid4()),
                                    "model": "claude-3-5-sonnet",
                                    "role": "assistant",
                                    "type": "message",
                                    "content": [{"type": "text", "text": content}]
                                },
                                "cwd": self.target_cwd,
                                "sessionId": self.session_id,
                                "version": "2.1.215",
                                "gitBranch": "dev"
                            }
                            records.append(record)
                            parent_uuid = cur_uuid
                except Exception:
                    pass

        print(f"✅ Generated {len(records)} Claude JSONL records.")

        with open(target_claude_jsonl, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

        print(f"🎉 Exported to Claude session file: {target_claude_jsonl}")
        return target_claude_jsonl
