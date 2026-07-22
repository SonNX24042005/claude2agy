import argparse
import sys
import os
import platform
import subprocess

try:
    from .converter import ClaudeToAgyConverter
    from .reverse_converter import AgyToClaudeConverter
    from .menu import select_option
    from . import __version__
except ImportError:
    from claude2agy.converter import ClaudeToAgyConverter
    from claude2agy.reverse_converter import AgyToClaudeConverter
    from claude2agy.menu import select_option
    from claude2agy import __version__

def update_tool():
    """Update Claude2AGY and AGY2Claude to the latest version from GitHub."""
    print("🔄 Checking for updates and updating Claude2AGY / AGY2Claude...")
    
    current_script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    install_dir = os.path.expanduser("~/.claude2agy")
    
    target_git_dir = None
    if os.path.exists(os.path.join(current_script_dir, ".git")):
        target_git_dir = current_script_dir
    elif os.path.exists(os.path.join(install_dir, ".git")):
        target_git_dir = install_dir

    if target_git_dir:
        print(f"📦 Git repository detected at: {target_git_dir}")
        print("🔄 Pulling latest changes from GitHub...")
        try:
            res = subprocess.run(["git", "-C", target_git_dir, "pull"], capture_output=True, text=True)
            if res.returncode == 0:
                print("✨ Update completed successfully!")
                print(res.stdout.strip())
                return True
            else:
                print(f"⚠️ Git pull notice: {res.stderr.strip()}")
        except Exception as e:
            print(f"⚠️ Git pull failed: {e}")

    # Fallback to online installer script
    print("📥 Running installer script to update...")
    is_windows = platform.system() == "Windows"
    
    local_installer_sh = os.path.join(current_script_dir, "install.sh")
    local_installer_ps = os.path.join(current_script_dir, "install.ps1")
    
    if not is_windows and os.path.exists(local_installer_sh):
        cmd = ["bash", local_installer_sh]
    elif is_windows and os.path.exists(local_installer_ps):
        cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", local_installer_ps]
    else:
        if is_windows:
            cmd = ["powershell", "-Command", "iwr -useb https://raw.githubusercontent.com/SonNX24042005/claude2agy/main/install.ps1 | iex"]
        else:
            cmd = ["bash", "-c", "curl -fsSL https://raw.githubusercontent.com/SonNX24042005/claude2agy/main/install.sh | bash"]

    try:
        res = subprocess.run(cmd)
        if res.returncode == 0:
            print("\n✨ Claude2AGY / AGY2Claude updated successfully to the latest version!")
            return True
        else:
            print("\n❌ Update failed. Please check your network connection or try running the installer manually.")
            return False
    except Exception as e:
        print(f"\n❌ Error during update: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Claude2AGY / AGY2Claude: Bi-directional Converter between Claude Code (.jsonl) and Antigravity CLI (agy) sessions."
    )
    parser.add_argument(
        "--file", "-f",
        default=None,
        help="Path to the Claude Code session .jsonl file."
    )
    parser.add_argument(
        "--reverse", "-r",
        action="store_true",
        help="Convert from Antigravity session to Claude Code (.jsonl) format."
    )
    parser.add_argument(
        "--session", "-s",
        default=None,
        help="Antigravity Session ID for reverse conversion."
    )
    parser.add_argument(
        "--cwd", "-c",
        default=os.getcwd(),
        help="Working directory path for the session (defaults to current directory)."
    )
    parser.add_argument(
        "--update", "-u",
        action="store_true",
        help="Update Claude2AGY and AGY2Claude to the latest version from GitHub."
    )
    parser.add_argument(
        "--version", "-v",
        action="store_true",
        help="Show version information."
    )

    args = parser.parse_args()

    if args.version:
        print(f"Claude2AGY / AGY2Claude v{__version__}")
        sys.exit(0)

    if args.update:
        success = update_tool()
        sys.exit(0 if success else 1)


    try:
        if args.reverse or sys.argv[0].endswith("agy2claude"):
            # REVERSE CONVERSION: AGY -> Claude Code
            print(f"🔄 Reverse Mode: Converting Antigravity session to Claude Code JSONL...")
            selected_session = args.session

            if not selected_session:
                sessions = AgyToClaudeConverter.get_agy_sessions(target_cwd=args.cwd)
                if not sessions:
                    print("❌ No Antigravity sessions found!", file=sys.stderr)
                    sys.exit(1)

                options_display = [f"{s['mtime']} | [{s['id'][:8]}] {s['preview'][:60]}" for s in sessions]
                title = "🔍 Select an Antigravity session to convert to Claude Code:"
                choice_idx = select_option(options_display, title=title)

                if choice_idx is None:
                    print("❌ Selection cancelled by user.")
                    sys.exit(0)

                selected_session = sessions[choice_idx]["id"]

            rev_converter = AgyToClaudeConverter(session_id=selected_session, target_cwd=args.cwd)
            exported_file = rev_converter.convert()

            print("\n" + "=" * 60)
            print("✨ REVERSE CONVERSION COMPLETED SUCCESSFULLY!")
            print(f"📌 Exported Claude JSONL: {exported_file}")
            print("=" * 60)

        else:
            # FORWARD CONVERSION: Claude Code -> AGY
            selected_file = args.file

            if not selected_file:
                project_name = os.path.basename(args.cwd)
                sessions = ClaudeToAgyConverter.get_project_sessions(target_cwd=args.cwd)

                if not sessions:
                    print(f"❌ No Claude session logs (.jsonl) found for project '{project_name}' in ~/.claude/projects/!", file=sys.stderr)
                    sys.exit(1)

                options_display = []
                for s in sessions:
                    prompt_snippet = s["first_prompt"][:75].replace("\n", " ")
                    if len(s["first_prompt"]) > 75:
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
            print("👉 Run either of the following commands in your terminal to open the session:")
            print(f"\n   agy -c")
            print(f"   agy --conversation {session_id}\n")
            print("=" * 60)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
