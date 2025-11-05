#!/usr/bin/env python3
"""Launcher script for Skill Scraper with UI mode selection."""

import sys
import questionary
from rich.console import Console
from rich.panel import Panel
from rich import box

console = Console()


def show_launcher_banner():
    """Display launcher banner."""
    banner = """[bold cyan]
╔═══════════════════════════════════════════════╗
║         🚀 SKILL SCRAPER LAUNCHER 🚀          ║
║                                               ║
║   Enhanced UI with multiple interface modes   ║
╚═══════════════════════════════════════════════╝
[/bold cyan]"""
    console.print(banner)
    console.print()


def main():
    """Main launcher function."""
    show_launcher_banner()

    mode = questionary.select(
        "🎨 Select your preferred interface:",
        choices=[
            questionary.Choice(
                "✨ Enhanced CLI - Rich terminal interface with colors and animations (recommended)",
                value="cli"
            ),
            questionary.Choice(
                "🖥️  TUI Mode - Full-screen terminal user interface (experimental)",
                value="tui"
            ),
            questionary.Choice(
                "❌ Exit",
                value="exit"
            ),
        ]
    ).ask()

    if mode == "cli":
        console.print("\n[cyan]🚀 Launching Enhanced CLI Mode...[/cyan]\n")
        from main import main as cli_main
        cli_main()

    elif mode == "tui":
        console.print("\n[cyan]🚀 Launching TUI Mode...[/cyan]\n")
        try:
            from tui import run_tui
            run_tui()
        except Exception as e:
            console.print(f"\n[red]❌ Error launching TUI: {e}[/red]")
            console.print("[yellow]💡 Falling back to Enhanced CLI mode...[/yellow]\n")
            from main import main as cli_main
            cli_main()

    elif mode == "exit" or mode is None:
        console.print("\n[green]👋 Thanks for using Skill Scraper![/green]\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
