import argparse
import sys
import os
from .converter import ClaudeToAgyConverter
from .menu import select_option

def main():
    parser = argparse.ArgumentParser(
        description="Claude2AGY: Convert Claude Code (.jsonl) chat sessions into native Antigravity CLI sessions."
    )
    parser.add_argument(
        "--file", "-f",
        default=None,
        help="Path to the Claude Code session .jsonl file (optional, opens interactive menu if omitted)."
    )
    parser.add_argument(
        "--cwd", "-c",
        default=os.getcwd(),
        help="Working directory path for the session (defaults to current directory)."
    )

    args = parser.parse_args()

    try:
        selected_file = args.file

        if not selected_file:
            project_name = os.path.basename(args.cwd)
            sessions = ClaudeToAgyConverter.get_project_sessions(target_cwd=args.cwd)

            if not sessions:
                print(f"❌ No Claude session logs (.jsonl) found for project '{project_name}' in ~/.claude/projects/!", file=sys.stderr)
                sys.exit(1)

            # Format options for interactive arrow key menu
            options_display = []
            for s in sessions:
                prompt_snippet = s["first_prompt"][:80].replace("\n", " ")
                if len(s["first_prompt"]) > 80:
                    prompt_snippet += "..."
                options_display.append(f"{s['mtime']} | {prompt_snippet}")

            title = f"🔍 Select a Claude Code session for project [{project_name}]:"
            choice_idx = select_option(options_display, title=title)

            if choice_idx is None:
                print("❌ Selection cancelled by user.")
                sys.exit(0)

            selected_file = sessions[choice_idx]["path"]
            print(f"✅ Selected session: {sessions[choice_idx]['filename']}\n")

        converter = ClaudeToAgyConverter(claude_jsonl_path=selected_file, target_cwd=args.cwd)
        converter.parse_claude_jsonl()
        session_id = converter.create_native_session()

        print("\n" + "=" * 60)
        print("✨ CONVERSION COMPLETED SUCCESSFULLY!")
        print(f"📌 Session ID: {session_id}")
        print("👉 Run the following command in your terminal to open the session:")
        print(f"\n   agy --conversation {session_id}\n")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
