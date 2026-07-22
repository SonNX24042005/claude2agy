import os
import json
import sqlite3
import subprocess
import glob
import re
import uuid
import shutil
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
        self.qa_pairs = []

        now_iso = datetime.now().isoformat() + "Z"
        curr_user_text = None
        curr_user_ts = now_iso
        curr_assistant_texts = []

        with open(self.claude_jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    if not self.session_id and data.get("sessionId"):
                        self.session_id = data.get("sessionId")

                    m_type = data.get("type")
                    msg = data.get("message", {})
                    timestamp = data.get("timestamp", now_iso)

                    if m_type == "user":
                        content = msg.get("content")
                        text_parts = []

                        if isinstance(content, str):
                            cleaned = self.clean_user_text(content)
                            if cleaned:
                                text_parts.append(cleaned)
                        elif isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict):
                                    # Ignore tool_result items in user messages
                                    if item.get("type") == "text":
                                        txt = self.clean_user_text(item.get("text", ""))
                                        if txt:
                                            text_parts.append(txt)

                        if text_parts:
                            full_user_text = "\n".join(text_parts).strip()
                            if full_user_text:
                                if curr_user_text is not None:
                                    asst_ans = "\n\n".join(curr_assistant_texts).strip()
                                    self.qa_pairs.append({
                                        "user": curr_user_text,
                                        "assistant": asst_ans,
                                        "timestamp": curr_user_ts
                                    })
                                    self.user_messages.append(curr_user_text)
                                    if asst_ans:
                                        self.assistant_messages.append(asst_ans)
                                curr_user_text = full_user_text
                                curr_user_ts = timestamp
                                curr_assistant_texts = []

                    elif m_type == "assistant":
                        content = msg.get("content")
                        if isinstance(content, str):
                            txt = content.strip()
                            if txt and txt != "No response requested.":
                                curr_assistant_texts.append(txt)
                        elif isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict) and item.get("type") == "text":
                                    txt = item.get("text", "").strip()
                                    if txt and txt != "No response requested.":
                                        curr_assistant_texts.append(txt)

                except Exception:
                    pass

        if curr_user_text is not None:
            asst_ans = "\n\n".join(curr_assistant_texts).strip()
            self.qa_pairs.append({
                "user": curr_user_text,
                "assistant": asst_ans,
                "timestamp": curr_user_ts
            })
            self.user_messages.append(curr_user_text)
            if asst_ans:
                self.assistant_messages.append(asst_ans)

        print(f"✅ Extracted {len(self.qa_pairs)} clean user-assistant QA turns.")

    @staticmethod
    def encode_varint(n):
        buf = bytearray()
        while True:
            towrite = n & 0x7f
            n >>= 7
            if n:
                buf.append(towrite | 0x80)
            else:
                buf.append(towrite)
                break
        return bytes(buf)

    @classmethod
    def build_user_payload(cls, template_payload, orig_text_bytes, new_text_str):
        new_bytes = new_text_str.encode("utf-8")
        pos1 = template_payload.find(orig_text_bytes)
        if pos1 == -1:
            return template_payload
        pos2 = template_payload.find(orig_text_bytes, pos1 + len(orig_text_bytes))
        if pos2 == -1:
            return template_payload

        part0 = template_payload[:pos1 - 1]
        part1 = template_payload[pos1 + len(orig_text_bytes) : pos2 - 1]
        part2 = template_payload[pos2 + len(orig_text_bytes):]

        return (
            part0 + 
            b"\x12" + cls.encode_varint(len(new_bytes)) + new_bytes + 
            part1 + 
            b"\x0a" + cls.encode_varint(len(new_bytes)) + new_bytes + 
            part2
        )

    @classmethod
    def build_assistant_payload(cls, template_payload, orig_text_bytes, new_text_str):
        new_bytes = new_text_str.encode("utf-8")
        pos1 = template_payload.find(orig_text_bytes)
        if pos1 == -1:
            return template_payload
        pos2 = template_payload.find(orig_text_bytes, pos1 + len(orig_text_bytes))
        if pos2 == -1:
            return template_payload

        part0 = template_payload[:pos1 - 1]
        part1 = template_payload[pos1 + len(orig_text_bytes) : pos2 - 1]
        part2 = template_payload[pos2 + len(orig_text_bytes):]

        return (
            part0 + 
            b"\x0a" + cls.encode_varint(len(new_bytes)) + new_bytes + 
            part1 + 
            b"\x42" + cls.encode_varint(len(new_bytes)) + new_bytes + 
            part2
        )

    def create_native_session(self):
        """Create native Antigravity CLI session with valid DB initialization, native TUI rendering, and 100% exact Claude transcript matching."""
        if not self.qa_pairs:
            raise ValueError("No valid user-assistant turns found in the Claude JSONL file!")

        print("🚀 Initializing native Antigravity session database...")

        conversations_dir = os.path.expanduser("~/.gemini/antigravity-cli/conversations")
        if not os.path.exists(conversations_dir):
            os.makedirs(conversations_dir, exist_ok=True)

        existing_dbs = set(f for f in os.listdir(conversations_dir) if f.endswith(".db") and not f.endswith(".db-shm") and not f.endswith(".db-wal"))

        init_prompt = "Initializing imported session history..."
        res = subprocess.run(
            ["agy", "--dangerously-skip-permissions", "-p", init_prompt],
            cwd=self.target_cwd,
            capture_output=True,
            text=True
        )

        current_dbs = set(f for f in os.listdir(conversations_dir) if f.endswith(".db") and not f.endswith(".db-shm") and not f.endswith(".db-wal"))
        new_dbs = list(current_dbs - existing_dbs)

        if new_dbs:
            new_session_id = new_dbs[0].replace(".db", "")
        else:
            db_files = [os.path.join(conversations_dir, f) for f in os.listdir(conversations_dir) if f.endswith(".db")]
            db_files.sort(key=os.path.getmtime, reverse=True)
            new_session_id = os.path.basename(db_files[0]).replace(".db", "")

        self.session_id = new_session_id
        print(f"🎉 Created Native Session ID: {new_session_id}")

        # Populate SQLite database steps table for AGY CLI TUI and /rewind support
        db_path = os.path.join(conversations_dir, f"{new_session_id}.db")
        last_u_idx = 0
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            rows = cur.execute("SELECT idx, step_type, status, metadata, step_payload FROM steps").fetchall()

            if len(rows) >= 3:
                u_meta_tpl, u_payload_tpl = rows[0][3], rows[0][4]
                a_meta_tpl, a_payload_tpl = rows[2][3], rows[2][4]

                uuids_u = re.findall(rb"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", u_meta_tpl)
                u_orig_step_uuid = uuids_u[0] if uuids_u else None

                uuids_a_payload = re.findall(rb"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", a_payload_tpl)
                a_orig_step_uuid = uuids_a_payload[3] if len(uuids_a_payload) > 3 else (uuids_a_payload[0] if uuids_a_payload else None)

                u_orig_text = init_prompt.encode("utf-8")
                a_orig_text = res.stdout.strip().encode("utf-8")

                cur.execute("DELETE FROM steps;")

                db_step_idx = 0
                for pair in self.qa_pairs:
                    u_t = pair.get("user", "").strip()
                    a_t = pair.get("assistant", "").strip()

                    if not u_t:
                        continue

                    turn_u_uuid = str(uuid.uuid4()).encode("utf-8")
                    turn_a_uuid = str(uuid.uuid4()).encode("utf-8")

                    # 1. Build USER_INPUT step
                    u_payload = self.build_user_payload(u_payload_tpl, u_orig_text, u_t)
                    u_meta = u_meta_tpl
                    if u_orig_step_uuid:
                        u_meta = u_meta.replace(u_orig_step_uuid, turn_u_uuid)
                        u_payload = u_payload.replace(u_orig_step_uuid, turn_u_uuid)

                    cur.execute(
                        "INSERT INTO steps (idx, step_type, status, has_subtrajectory, metadata, error_details, permissions, task_details, render_info, step_payload, step_format) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (db_step_idx, 14, 3, "false", u_meta, None, None, None, None, u_payload, 0)
                    )
                    last_u_idx = db_step_idx
                    db_step_idx += 1

                    # 2. Build PLANNER_RESPONSE step linked to turn_u_uuid
                    asst_text = a_t if a_t else "Completed."
                    a_payload = self.build_assistant_payload(a_payload_tpl, a_orig_text, asst_text)
                    a_meta = a_meta_tpl
                    if a_orig_step_uuid:
                        a_meta = a_meta.replace(a_orig_step_uuid, turn_a_uuid)
                        a_payload = a_payload.replace(a_orig_step_uuid, turn_a_uuid)
                    if u_orig_step_uuid:
                        a_meta = a_meta.replace(u_orig_step_uuid, turn_u_uuid)
                        a_payload = a_payload.replace(u_orig_step_uuid, turn_u_uuid)

                    cur.execute(
                        "INSERT INTO steps (idx, step_type, status, has_subtrajectory, metadata, error_details, permissions, task_details, render_info, step_payload, step_format) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (db_step_idx, 15, 3, "false", a_meta, None, None, None, None, a_payload, 0)
                    )
                    db_step_idx += 1

                conn.commit()
            conn.close()

        except Exception as e:
            print(f"⚠️ Warning updating SQLite steps DB: {e}")

        # Write exact native transcript steps to brain/<session_id>/.system_generated/logs/
        brain_dir = os.path.expanduser(f"~/.gemini/antigravity-cli/brain/{new_session_id}/.system_generated/logs")
        os.makedirs(brain_dir, exist_ok=True)

        transcript_path = os.path.join(brain_dir, "transcript.jsonl")
        transcript_full_path = os.path.join(brain_dir, "transcript_full.jsonl")

        now_iso = datetime.now().isoformat() + "Z"

        # Build comprehensive CHECKPOINT summary content listing ALL user prompts
        user_prompts_summary_lines = []
        for idx, pair in enumerate(self.qa_pairs):
            u_str = pair.get("user", "").strip().replace("\n", " ")
            if len(u_str) > 120:
                u_str = u_str[:120] + "..."
            user_prompts_summary_lines.append(f"{idx + 1}. {u_str}")

        prompt_summary_text = "\n".join(user_prompts_summary_lines)
        first_u = self.qa_pairs[0].get("user", "").strip() if self.qa_pairs else "Imported Claude Session"

        cp_content = (
            f"{{{{ CHECKPOINT 0 }}}}\n\n"
            f"# USER Objective:\n{first_u[:200]}\n\n"
            f"# Complete User Prompts History ({len(self.qa_pairs)} prompts imported):\n"
            f"{prompt_summary_text}\n"
        )

        steps = []
        step_idx = 0

        # Exact 1-to-1 mapping with SQLite steps table indices
        for i, pair in enumerate(self.qa_pairs):
            u_text = pair.get("user", "")
            a_text = pair.get("assistant", "")
            ts = pair.get("timestamp", now_iso)

            if not u_text or not u_text.strip():
                continue

            steps.append({
                "step_index": step_idx,
                "source": "USER_EXPLICIT",
                "type": "USER_INPUT",
                "status": "DONE",
                "created_at": ts,
                "content": f"<USER_REQUEST>\n{u_text.strip()}\n</USER_REQUEST>"
            })
            step_idx += 1

            asst_content = a_text.strip() if a_text and a_text.strip() else "Completed."
            steps.append({
                "step_index": step_idx,
                "source": "MODEL",
                "type": "PLANNER_RESPONSE",
                "status": "DONE",
                "created_at": ts,
                "content": asst_content
            })
            step_idx += 1

        # Append CHECKPOINT step aligned with final step_idx
        steps.append({
            "step_index": step_idx,
            "source": "SYSTEM",
            "type": "CHECKPOINT",
            "status": "DONE",
            "created_at": now_iso,
            "content": cp_content
        })

        # Add matching CHECKPOINT row to SQLite steps DB to keep indices 100% in sync
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO steps (idx, step_type, status, has_subtrajectory, metadata, error_details, permissions, task_details, render_info, step_payload, step_format) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (step_idx, 98, 3, "false", None, None, None, None, None, None, 0)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ Warning appending CHECKPOINT to SQLite steps DB: {e}")

        with open(transcript_path, "w", encoding="utf-8") as f:
            for s in steps:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")

        with open(transcript_full_path, "w", encoding="utf-8") as f:
            for s in steps:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")

        self.register_in_summaries(new_session_id)
        return new_session_id

    def register_in_summaries(self, session_id):
        """Register the converted session in SQLite conversation_summaries.db for AGY CLI."""
        target_path = os.path.expanduser("~/.gemini/antigravity-cli")
        os.makedirs(target_path, exist_ok=True)
        summary_db = os.path.join(target_path, "conversation_summaries.db")

        try:
            conn = sqlite3.connect(summary_db)
            cursor = conn.cursor()

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_summaries (
                conversation_id TEXT PRIMARY KEY,
                title TEXT,
                preview TEXT,
                step_count INTEGER,
                last_modified_time TEXT,
                workspace_uris TEXT,
                status TEXT,
                source TEXT,
                project_id TEXT,
                agent_name TEXT,
                parent_conversation_id TEXT,
                nesting_depth INTEGER,
                battle_id TEXT,
                winning_conversation_id TEXT,
                not_fully_idle INTEGER,
                killed INTEGER,
                last_user_input_time TEXT,
                last_user_input_step_index INTEGER,
                app_data_dir TEXT
            )
            """)

            first_msg = self.user_messages[0] if self.user_messages else "Imported Claude Session"
            preview_text = first_msg[:100]
            title_text = first_msg[:80]
            workspace_uri = f'["file://{self.target_cwd}"]'
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S+00:00")

            cursor.execute("PRAGMA table_info(conversation_summaries)")
            cols = [row[1] for row in cursor.fetchall()]

            last_u_index = (len(self.qa_pairs) - 1) * 2 if self.qa_pairs else 0
            base_values = {
                "conversation_id": session_id,
                "title": title_text,
                "preview": preview_text,
                "step_count": len(self.qa_pairs) * 2 + 1,
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
                "last_user_input_step_index": last_u_index,
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
        except Exception as e:
            print(f"⚠️  Warning registering in {summary_db}: {e}")

        # Update conversation_metadata.json cache for AGY CLI
        cache_json = os.path.expanduser("~/.gemini/antigravity-cli/cache/conversation_metadata.json")
        try:
            os.makedirs(os.path.dirname(cache_json), exist_ok=True)
            data = {}
            if os.path.exists(cache_json):
                with open(cache_json, "r", encoding="utf-8") as f:
                    data = json.load(f)

            first_msg = self.user_messages[0] if self.user_messages else "Imported Claude Session"
            now_iso = datetime.now().isoformat() + "Z"

            data[session_id] = {
                "summary": {
                    "ID": session_id,
                    "Title": "",
                    "Preview": first_msg[:100],
                    "NumSteps": len(self.qa_pairs) * 2 + 1,
                    "Loaded": True,
                    "UpdatedAt": now_iso,
                    "WorkspaceURIs": [f"file://{self.target_cwd}"],
                    "AppDataDir": "antigravity-cli",
                    "ProjectID": "default-cli-project",
                    "AgentName": ""
                },
                "is_internal": False,
                "last_modified_time": now_iso
            }

            with open(cache_json, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  Warning updating cache {cache_json}: {e}")

        print("✅ Registered session for AGY CLI context memory.")



