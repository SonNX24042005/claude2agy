import os
import json
import sqlite3
import subprocess
import glob
from datetime import datetime

class ClaudeToAgyConverter:
    def __init__(self, claude_jsonl_path=None, target_cwd=None):
        self.target_cwd = os.path.abspath(target_cwd or os.getcwd())
        self.claude_jsonl_path = os.path.abspath(claude_jsonl_path) if claude_jsonl_path else None
        self.user_messages = []
        self.assistant_messages = []
        self.session_id = None

    @staticmethod
    def get_project_sessions(target_cwd=None):
        """Discover and list all Claude session logs matching the project folder."""
        target_cwd = os.path.abspath(target_cwd or os.getcwd())
        folder_name = os.path.basename(target_cwd)
        sanitized = target_cwd.strip("/").replace("/", "-")
        
        projects_dir = os.path.expanduser("~/.claude/projects")
        if not os.path.exists(projects_dir):
            return []

        matching_dirs = []
        for d in os.listdir(projects_dir):
            full_p = os.path.join(projects_dir, d)
            if os.path.isdir(full_p):
                if folder_name in d or d in sanitized or sanitized in d:
                    matching_dirs.append(full_p)

        jsonl_files = []
        for md in matching_dirs:
            jsonl_files.extend(glob.glob(os.path.join(md, "*.jsonl")))

        jsonl_files.sort(key=os.path.getmtime, reverse=True)

        sessions = []
        for fp in jsonl_files:
            mtime_str = datetime.fromtimestamp(os.path.getmtime(fp)).strftime("%Y-%m-%d %H:%M")
            first_prompt = "Unknown prompt"
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    for line in f:
                        data = json.loads(line)
                        if data.get("type") == "user":
                            c = data.get("message", {}).get("content")
                            txt = ""
                            if isinstance(c, list):
                                txt = "".join([item.get("text", "") for item in c if isinstance(item, dict)])
                            elif isinstance(c, str):
                                txt = c
                            
                            # Clean prompt text
                            if txt and not txt.startswith("<local-command") and not txt.startswith("<command-name>") and not txt.startswith("<task-notification>"):
                                if "<ide_opened_file>" in txt:
                                    txt = txt.split("</ide_opened_file>")[-1]
                                txt = txt.strip()
                                if txt:
                                    first_prompt = txt.replace("\n", " ")
                                    break
            except Exception:
                pass

            sessions.append({
                "path": fp,
                "mtime": mtime_str,
                "first_prompt": first_prompt,
                "filename": os.path.basename(fp)
            })

        return sessions

    def parse_claude_jsonl(self):
        """Parse all user requests and assistant messages from Claude JSONL."""
        if not self.claude_jsonl_path or not os.path.exists(self.claude_jsonl_path):
            raise FileNotFoundError(f"Claude JSONL file not found: {self.claude_jsonl_path}")

        print(f"📖 Parsing Claude JSONL log: {self.claude_jsonl_path}")

        with open(self.claude_jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    raw = json.loads(line)
                    if not self.session_id and raw.get("sessionId"):
                        self.session_id = raw.get("sessionId")

                    m_type = raw.get("type")
                    msg = raw.get("message", {})

                    if m_type == "user":
                        content = msg.get("content")
                        text = ""
                        if isinstance(content, list):
                            text = "".join([item.get("text", "") for item in content if isinstance(item, dict)])
                        else:
                            text = str(content) if content else ""

                        if text and not text.startswith("<local-command") and not text.startswith("<command-name>") and not text.startswith("<task-notification>"):
                            if "<ide_opened_file>" in text:
                                text = text.split("</ide_opened_file>")[-1]
                            text = text.strip()
                            if text:
                                self.user_messages.append(text)

                    elif m_type == "assistant":
                        content = msg.get("content")
                        text = ""
                        if isinstance(content, list):
                            text_parts = [item.get("text", "") for item in content if isinstance(item, dict) and item.get("type") == "text"]
                            text = "\n".join(text_parts)
                        elif isinstance(content, str):
                            text = content

                        if text and text != "No response requested.":
                            self.assistant_messages.append(text)
                except Exception:
                    pass

        print(f"✅ Found {len(self.user_messages)} user prompts and {len(self.assistant_messages)} assistant responses.")

    def create_native_session(self):
        """Create and seed the native Antigravity CLI session with auto-permissions for full rendering."""
        if not self.user_messages:
            raise ValueError("No user prompts found in the Claude JSONL file!")

        first_prompt = self.user_messages[0]
        print("🚀 Initializing native Antigravity session with auto-permissions...")
        
        # Use --dangerously-skip-permissions to ensure full AI responses complete without stalling on prompts
        res = subprocess.run(["agy", "--dangerously-skip-permissions", "-p", first_prompt], cwd=self.target_cwd, capture_output=True, text=True)
        
        conversations_dir = os.path.expanduser("~/.gemini/antigravity-cli/conversations")
        if not os.path.exists(conversations_dir):
            os.makedirs(conversations_dir, exist_ok=True)

        db_files = [os.path.join(conversations_dir, f) for f in os.listdir(conversations_dir) if f.endswith(".db")]
        db_files.sort(key=os.path.getmtime, reverse=True)

        if not db_files:
            raise RuntimeError("Failed to locate newly created conversation database!")

        new_session_id = os.path.basename(db_files[0]).replace(".db", "")
        print(f"🎉 Created Native Session ID: {new_session_id}")

        if len(self.user_messages) > 1:
            print(f"⏳ Seeding remaining {len(self.user_messages) - 1} prompts with full AI responses...")
            for idx, prompt in enumerate(self.user_messages[1:], start=2):
                print(f"   [{idx}/{len(self.user_messages)}] Seeding prompt: {prompt[:80]}...")
                subprocess.run(["agy", "--dangerously-skip-permissions", "--conversation", new_session_id, "-p", prompt], cwd=self.target_cwd, capture_output=True, text=True)

        self.register_in_summaries(new_session_id)
        return new_session_id

    def register_in_summaries(self, session_id):
        """Register the converted session in SQLite conversation_summaries.db."""
        summary_db = os.path.expanduser("~/.gemini/antigravity-cli/conversation_summaries.db")
        if not os.path.exists(summary_db):
            return

        try:
            conn = sqlite3.connect(summary_db)
            cursor = conn.cursor()

            preview_text = self.user_messages[0][:50] if self.user_messages else "Imported Claude Session"
            workspace_uri = f'["file://{self.target_cwd}"]'

            sql = """
            INSERT OR REPLACE INTO conversation_summaries (
                conversation_id, title, preview, step_count, last_modified_time,
                workspace_uris, status, source, project_id, agent_name,
                parent_conversation_id, nesting_depth, battle_id, winning_conversation_id,
                not_fully_idle, killed, last_user_input_time, last_user_input_step_index, app_data_dir
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            values = (
                session_id, "", preview_text, len(self.user_messages),
                "2026-07-21 14:40:00+00:00", workspace_uri, "", "",
                "default-cli-project", "", "", 0, "", "", 0, 0,
                "2026-07-21 14:40:00+00:00", 0, "antigravity-cli"
            )

            cursor.execute(sql, values)
            conn.commit()
            conn.close()
            print("✅ Registered session in conversation_summaries.db")
        except Exception as e:
            print(f"⚠️ Warning registering in summaries db: {e}")
