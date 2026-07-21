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
        self.turns = []
        self.session_id = None

    @staticmethod
    def get_project_sessions(target_cwd=None):
        """Discover and list ALL Claude session logs strictly belonging to the target project folder."""
        target_cwd = os.path.abspath(target_cwd or os.getcwd())
        sanitized = "-" + target_cwd.strip("/").replace("/", "-")
        
        projects_dir = os.path.expanduser("~/.claude/projects")
        if not os.path.exists(projects_dir):
            return []

        # Find matching directory strictly for the current project
        matching_dirs = []
        target_folder = os.path.join(projects_dir, sanitized)

        if os.path.exists(target_folder):
            matching_dirs.append(target_folder)
        else:
            # Fallback strict directory name match
            for d in os.listdir(projects_dir):
                if d == sanitized:
                    matching_dirs.append(os.path.join(projects_dir, d))

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

    @staticmethod
    def clean_user_text(text):
        """Clean and filter internal system/tool tags from user message strings."""
        if not text or not isinstance(text, str):
            return ""
        import re
        # Ignore system/tool notifications and local command output blocks
        if re.match(r"^\s*<(local-command|command-name|command-message|command-stdout|local-command-caveat|task-notification)", text):
            return ""
        if "<ide_opened_file>" in text:
            text = text.split("</ide_opened_file>")[-1]
        return text.strip()

    def parse_claude_jsonl(self):
        """Parse all user requests and assistant messages in chronological order from Claude JSONL."""
        if not self.claude_jsonl_path or not os.path.exists(self.claude_jsonl_path):
            raise FileNotFoundError(f"Claude JSONL file not found: {self.claude_jsonl_path}")

        print(f"📖 Parsing Claude JSONL log: {self.claude_jsonl_path}")

        self.turns = []
        self.user_messages = []
        self.assistant_messages = []

        now_iso = datetime.now().isoformat() + "Z"

        with open(self.claude_jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    raw = json.loads(line)
                    if not self.session_id and raw.get("sessionId"):
                        self.session_id = raw.get("sessionId")

                    m_type = raw.get("type")
                    msg = raw.get("message", {})
                    timestamp = raw.get("timestamp", now_iso)

                    if m_type == "user":
                        content = msg.get("content")
                        text = ""
                        if isinstance(content, list):
                            text = "".join([item.get("text", "") for item in content if isinstance(item, dict) and item.get("type") == "text"])
                        elif isinstance(content, str):
                            text = content

                        cleaned = self.clean_user_text(text)
                        if cleaned:
                            self.user_messages.append(cleaned)
                            self.turns.append({
                                "role": "user",
                                "content": cleaned,
                                "timestamp": timestamp
                            })

                    elif m_type == "assistant":
                        content = msg.get("content")
                        text_parts = []
                        if isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict) and item.get("type") == "text":
                                    text_parts.append(item.get("text", ""))
                        elif isinstance(content, str):
                            text_parts.append(content)

                        text = "\n".join(text_parts).strip()
                        if text and text != "No response requested.":
                            self.assistant_messages.append(text)
                            self.turns.append({
                                "role": "assistant",
                                "content": text,
                                "timestamp": timestamp
                            })
                except Exception:
                    pass

        print(f"✅ Found {len(self.user_messages)} user prompts and {len(self.assistant_messages)} assistant responses.")

    def create_native_session(self):
        """Create native Antigravity CLI session with valid DB initialization and 100% exact Claude transcript matching."""
        if not self.turns:
            raise ValueError("No user prompts or responses found in the Claude JSONL file!")

        print("🚀 Initializing native Antigravity session database...")

        # 1. Run agy ONCE to initialize valid SQLite database in ~/.gemini/antigravity-cli/conversations/
        init_prompt = self.user_messages[0] if self.user_messages else "Initializing converted session"
        res = subprocess.run(
            ["agy", "--dangerously-skip-permissions", "-p", f"Initializing session: {init_prompt[:40]}"],
            cwd=self.target_cwd,
            capture_output=True,
            text=True
        )

        conversations_dir = os.path.expanduser("~/.gemini/antigravity-cli/conversations")
        if not os.path.exists(conversations_dir):
            os.makedirs(conversations_dir, exist_ok=True)

        db_files = [os.path.join(conversations_dir, f) for f in os.listdir(conversations_dir) if f.endswith(".db")]
        db_files.sort(key=os.path.getmtime, reverse=True)

        if not db_files:
            raise RuntimeError("Failed to locate newly created conversation database!")

        new_session_id = os.path.basename(db_files[0]).replace(".db", "")
        self.session_id = new_session_id
        print(f"🎉 Created Native Session ID: {new_session_id}")

        # 2. Write exact 100% matched transcript to brain/<session_id>/.system_generated/logs/
        brain_dir = os.path.expanduser(f"~/.gemini/antigravity-cli/brain/{new_session_id}/.system_generated/logs")
        os.makedirs(brain_dir, exist_ok=True)

        transcript_path = os.path.join(brain_dir, "transcript.jsonl")
        transcript_full_path = os.path.join(brain_dir, "transcript_full.jsonl")

        # ── Group turns into clean 1-to-1 QA pairs ────────────────────────────
        now_iso = datetime.now().isoformat() + "Z"
        qa_pairs = []
        curr_user = None
        curr_asst_parts = []

        for turn in self.turns:
            ts = turn.get("timestamp", now_iso)
            if turn["role"] == "user":
                if curr_user is not None:
                    asst_full = "\n\n".join(curr_asst_parts).strip()
                    qa_pairs.append((curr_user, asst_full))
                curr_user = turn["content"]
                curr_asst_parts = []
            elif turn["role"] == "assistant":
                if turn["content"]:
                    curr_asst_parts.append(turn["content"])

        if curr_user is not None:
            asst_full = "\n\n".join(curr_asst_parts).strip()
            qa_pairs.append((curr_user, asst_full))

        if not qa_pairs:
            raise ValueError("No valid user-assistant pairs could be constructed!")

        first_prompt, first_response = qa_pairs[0]

        # ── Build Summary for CONVERSATION_HISTORY step ───────────────────────
        user_requests_summary = "\n".join(
            f"{i+1}. {u}" for i, (u, _) in enumerate(qa_pairs)
        )
        conv_history_content = (
            f"# Imported Conversation History ({len(qa_pairs)} user prompts)\n\n"
            f"Chronological list of all user prompts in this imported Claude Code session:\n\n"
            f"{user_requests_summary}"
        )

        # ── Assemble transcript steps ─────────────────────────────────────────
        steps = []
        step_idx = 0

        # Step 0: First user prompt
        first_turn_ts = self.turns[0].get("timestamp", now_iso)
        steps.append({
            "step_index": step_idx,
            "source": "USER_EXPLICIT",
            "type": "USER_INPUT",
            "status": "DONE",
            "created_at": first_turn_ts,
            "content": f"<USER_REQUEST>\n{first_prompt}\n</USER_REQUEST>"
        })
        step_idx += 1

        # Step 1: CONVERSATION_HISTORY with summary
        steps.append({
            "step_index": step_idx,
            "source": "SYSTEM",
            "type": "CONVERSATION_HISTORY",
            "status": "DONE",
            "created_at": first_turn_ts,
            "content": conv_history_content
        })
        step_idx += 1

        # Step 2: First assistant response
        if first_response:
            steps.append({
                "step_index": step_idx,
                "source": "MODEL",
                "type": "PLANNER_RESPONSE",
                "status": "DONE",
                "created_at": first_turn_ts,
                "content": first_response
            })
            step_idx += 1

        # Step 3+: Remaining QA pairs
        for u_text, a_text in qa_pairs[1:]:
            steps.append({
                "step_index": step_idx,
                "source": "USER_EXPLICIT",
                "type": "USER_INPUT",
                "status": "DONE",
                "created_at": now_iso,
                "content": f"<USER_REQUEST>\n{u_text}\n</USER_REQUEST>"
            })
            step_idx += 1

            if a_text:
                steps.append({
                    "step_index": step_idx,
                    "source": "MODEL",
                    "type": "PLANNER_RESPONSE",
                    "status": "DONE",
                    "created_at": now_iso,
                    "content": a_text
                })
                step_idx += 1

        with open(transcript_path, "w", encoding="utf-8") as f:
            for s in steps:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")

        with open(transcript_full_path, "w", encoding="utf-8") as f:
            for s in steps:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")

        self.session_id = new_session_id
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

            first_msg = self.user_messages[0] if self.user_messages else "Imported Claude Session"
            preview_text = first_msg[:100]
            title_text = first_msg[:80]
            workspace_uri = f'["file://{self.target_cwd}"]'
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S+00:00")

            cursor.execute("PRAGMA table_info(conversation_summaries)")
            cols = [row[1] for row in cursor.fetchall()]

            base_values = {
                "conversation_id": session_id,
                "title": title_text,
                "preview": preview_text,
                "step_count": len(self.turns) + 1,
                "last_modified_time": now_str,
                "workspace_uris": workspace_uri,
                "status": "",
                "source": "",
                "project_id": "default-cli-project",
                "agent_name": "",
                "parent_conversation_id": "",
                "nesting_depth": 0,
                "battle_id": "",
                "winning_conversation_id": "",
                "not_fully_idle": 0,
                "killed": 0,
                "last_user_input_time": now_str,
                "last_user_input_step_index": 0,
                "app_data_dir": "antigravity-cli",
            }

            insert_cols = [c for c in cols if c in base_values]
            placeholders = ", ".join(["?"] * len(insert_cols))
            col_names = ", ".join(insert_cols)
            values = tuple(base_values[c] for c in insert_cols)

            cursor.execute(
                f"INSERT OR REPLACE INTO conversation_summaries ({col_names}) VALUES ({placeholders})",
                values
            )
            conn.commit()
            conn.close()
            print("✅ Registered session in conversation_summaries.db")
        except Exception as e:
            print(f"⚠️  Warning registering in summaries db: {e}")



