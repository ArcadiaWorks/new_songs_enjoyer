#!/usr/bin/env python3
"""
Simple task runner for new_songs_enjoyer
Alternative to justfile/Makefile for systems without just/make

Usage: python run.py <command> [args]
"""

import sys
import os
import subprocess
from pathlib import Path


def run_command(cmd, description=""):
    """Run a shell command and return success status."""
    if description:
        print(f"🔄 {description}")

    try:
        result = subprocess.run(cmd, shell=True, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        return False


def print_header(text):
    """Print a formatted header."""
    print(f"\n🎵 {text}")
    print("=" * (len(text) + 4))


def setup():
    """Complete initial setup."""
    print_header("Setting up new_songs_enjoyer...")

    # Copy .env.example to .env
    if not Path(".env").exists():
        if Path(".env.example").exists():
            run_command("cp .env.example .env", "Creating .env file")
            print("✅ Created .env file - please add your API keys")
        else:
            print("❌ .env.example not found")
            return False
    else:
        print("✅ .env file already exists")

    # Install dependencies
    if run_command("uv sync", "Installing dependencies"):
        print("✅ Dependencies installed")
        print("📝 Next: Edit .env file with your Last.fm API key")
        return True
    else:
        print("❌ Failed to install dependencies")
        return False


def generate(args):
    """Generate playlist with optional arguments."""
    cmd = "uv run python main.py"
    if args:
        cmd += " " + " ".join(args)

    print("🎵 Generating playlist...")
    return run_command(cmd)


def generate_preset(preset_name, tags, num_tracks):
    """Generate playlist with preset configuration."""
    emoji_map = {
        "chill": "😌",
        "rock": "🎸",
        "electronic": "🎛️",
        "jazz": "🎺",
        "pop": "🎤",
    }

    emoji = emoji_map.get(preset_name, "🎵")
    print(f"{emoji} Generating {preset_name} playlist...")

    cmd = f"uv run python main.py --tags {tags} --num-tracks {num_tracks}"
    return run_command(cmd)


def server():
    """Start web server."""
    print("🌐 Starting web server for SoundCloud integration...")
    print("📍 Access at: http://localhost:5000")

    # Import and run the web server directly
    try:
        import sys
        import os
        from pathlib import Path

        # Add current directory to Python path
        current_dir = Path(__file__).parent
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))

        # Import and run the web server
        from web_server import app, logger

        print("🎵 new_songs_enjoyer Web Server")
        print("=" * 40)
        print("Starting web server for SoundCloud integration...")
        print("Access your playlists at: http://localhost:5000")
        print("Press Ctrl+C to stop the server")
        print("=" * 40)

        app.run(debug=True, host="0.0.0.0", port=5000)

    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        return True
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False


def clean():
    """Clean cache files."""
    print("🧹 Cleaning up generated files...")

    # Remove cache directories
    cache_dirs = [
        "__pycache__",
        ".pytest_cache",
        "entities/__pycache__",
        "adapter/__pycache__",
    ]
    for cache_dir in cache_dirs:
        if Path(cache_dir).exists():
            run_command(f"rm -rf {cache_dir}")

    # Remove .pyc files
    run_command('find . -name "*.pyc" -delete')
    print("✅ Cleanup complete")


def clean_output():
    """Clean output directory."""
    print("🗑️ Cleaning output directory...")
    run_command("rm -f output/*.json output/*.html")
    print("✅ Output directory cleaned")


def show_playlists():
    """Show available playlists."""
    print("📋 Available playlists:")
    output_dir = Path("output")
    if output_dir.exists():
        html_files = list(output_dir.glob("*.html"))
        if html_files:
            for html_file in html_files:
                print(f"   {html_file.name}")
        else:
            print("   No playlists found. Run 'python run.py generate' first.")
    else:
        print("   Output directory doesn't exist.")


def test_config():
    """Test configuration."""
    print("🔍 Testing configuration...")

    # Check if .env exists
    if not Path(".env").exists():
        print("❌ .env file not found. Run 'python run.py setup' first.")
        return False

    print("✅ .env file exists")

    # Check API key configuration
    with open(".env", "r") as f:
        env_content = f.read()

    if "YOUR_LASTFM_API_KEY_HERE" in env_content:
        print("⚠️  Please update LASTFM_API_KEY in .env file")
    else:
        print("✅ Last.fm API key configured")

    if "YOUR_SOUNDCLOUD" in env_content:
        print("⚠️  SoundCloud credentials not configured (optional)")
    else:
        print("✅ SoundCloud credentials configured")

    return True


def status():
    """Show project status."""
    print_header("Project Status")

    # Check environment
    if Path(".env").exists():
        print("✅ Environment configured")
    else:
        print("❌ Environment not set up")

    # Check playlists
    output_dir = Path("output")
    if output_dir.exists() and list(output_dir.glob("*.html")):
        count = len(list(output_dir.glob("*.html")))
        print(f"✅ Playlists generated ({count} files)")
    else:
        print("📝 No playlists generated yet")

    # Check uv
    try:
        subprocess.run(["uv", "--version"], capture_output=True, check=True)
        print("✅ uv available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ uv not found")

    print("\n🚀 Quick Start:")
    print("   python run.py setup      - Initial setup")
    print("   python run.py generate   - Generate playlist")
    print("   python run.py server     - Start web interface")


def info():
    """Show project information."""
    print_header("new_songs_enjoyer - Music Discovery Tool")
    print()
    print("📁 Project Structure:")
    print("   main.py           - Core playlist generation")
    print("   web_server.py     - Web interface for SoundCloud")
    print("   entities/         - Data models")
    print("   adapter/          - SoundCloud integration")
    print("   templates/        - HTML templates")
    print("   output/           - Generated playlists")
    print()
    print("🔧 Configuration:")
    print("   .env              - API keys and secrets")
    print("   config.yaml       - Application settings")
    print()
    print("📖 Documentation:")
    print("   README.md         - Main documentation")
    print("   SOUNDCLOUD_SETUP.md - SoundCloud integration guide")
    print("   USAGE.md          - Usage examples")


def help_cmd():
    """Show help information."""
    print_header("new_songs_enjoyer - Available Commands")
    print()
    print("🏗️  Setup & Installation:")
    print("   python run.py setup           - Complete initial setup")
    print("   python run.py install         - Install dependencies only")
    print()
    print("🎵 Playlist Generation:")
    print(
        "   python run.py generate [args] - Generate playlist with optional arguments"
    )
    print("   python run.py generate-chill  - Generate chill/ambient playlist")
    print("   python run.py generate-rock   - Generate rock playlist")
    print("   python run.py generate-electronic - Generate electronic playlist")
    print("   python run.py generate-jazz   - Generate jazz playlist")
    print("   python run.py generate-pop    - Generate pop playlist")
    print()
    print("🌐 Web Server:")
    print("   python run.py server          - Start web server for SoundCloud")
    print()
    print("🧹 Maintenance:")
    print("   python run.py clean           - Clean cache files")
    print("   python run.py clean-output    - Clean generated playlists")
    print("   python run.py show-playlists  - List generated playlists")
    print()
    print("🧪 Testing:")
    print("   python run.py test-config     - Validate configuration")
    print()
    print("ℹ️  Information:")
    print("   python run.py info            - Show project information")
    print("   python run.py status          - Show project status")
    print("   python run.py help            - Show this help")
    print()
    print("📝 Examples:")
    print("   python run.py generate --tags indie rock --num-tracks 5")
    print("   python run.py generate-chill")
    print("   python run.py server")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        help_cmd()
        return

    command = sys.argv[1]
    args = sys.argv[2:] if len(sys.argv) > 2 else []

    # Command mapping
    commands = {
        "setup": setup,
        "install": lambda: run_command("uv sync", "Installing dependencies"),
        "generate": lambda: generate(args),
        "generate-chill": lambda: generate_preset("chill", "chill ambient lofi", 10),
        "generate-rock": lambda: generate_preset("rock", "rock indie alternative", 8),
        "generate-electronic": lambda: generate_preset(
            "electronic", "electronic techno house", 12
        ),
        "generate-jazz": lambda: generate_preset("jazz", "jazz blues soul", 6),
        "generate-pop": lambda: generate_preset("pop", "pop indie-pop synthpop", 10),
        "server": server,
        "clean": clean,
        "clean-output": clean_output,
        "show-playlists": show_playlists,
        "test-config": test_config,
        "status": status,
        "info": info,
        "help": help_cmd,
    }

    if command in commands:
        try:
            commands[command]()
        except KeyboardInterrupt:
            print("\n❌ Command interrupted by user")
        except Exception as e:
            print(f"❌ Error running command '{command}': {e}")
    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python run.py help' to see available commands")
        sys.exit(1)


if __name__ == "__main__":
    main()
