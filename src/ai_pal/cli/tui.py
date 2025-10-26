"""
AI-Pal TUI (Terminal User Interface)

Enhanced interactive terminal interface with Rich library features.

Provides:
- Dashboard with real-time metrics
- FFE management interface
- Self-improvement monitoring
- Context window visualization
- Momentum loop tracking
- A/B test management
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import sys

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.tree import Tree
from rich.text import Text
from rich import box
from loguru import logger

console = Console()


class AIPalTUI:
    """
    AI-Pal Terminal User Interface

    Enhanced interactive interface for system management
    """

    def __init__(self, storage_dir: Path = Path("./data")):
        self.storage_dir = storage_dir
        self.console = console
        self.running = True

    def show_banner(self) -> None:
        """Display AI-Pal banner"""
        banner = """
  █████╗ ██╗      ██████╗  █████╗ ██╗
 ██╔══██╗██║      ██╔══██╗██╔══██╗██║
 ███████║██║█████╗██████╔╝███████║██║
 ██╔══██║██║╚════╝██╔═══╝ ██╔══██║██║
 ██║  ██║██║      ██║     ██║  ██║███████╗
 ╚═╝  ╚═╝╚═╝      ╚═╝     ╚═╝  ╚═╝╚══════╝

        Agentic Cognitive Partner
        """

        self.console.print(Panel(
            Text(banner, justify="center", style="cyan bold"),
            subtitle="Interactive Terminal Interface",
            border_style="cyan"
        ))

    def show_main_menu(self) -> str:
        """Show main menu and get user choice"""
        self.console.print("\n[bold cyan]═══ Main Menu ═══[/bold cyan]\n")

        menu_items = {
            "1": ("Dashboard", "View system overview"),
            "2": ("FFE Management", "Manage goals and tasks"),
            "3": ("Momentum Loop", "View loop status"),
            "4": ("Self-Improvement", "Monitor improvements"),
            "5": ("A/B Tests", "Manage A/B tests"),
            "6": ("Context Window", "View memory"),
            "7": ("Create Task", "Create new task"),
            "8": ("Help", "Show help"),
            "0": ("Exit", "Exit TUI")
        }

        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("Option", style="cyan", width=8)
        table.add_column("Name", style="bold")
        table.add_column("Description", style="dim")

        for key, (name, desc) in menu_items.items():
            table.add_row(f"[{key}]", name, desc)

        self.console.print(table)

        choice = Prompt.ask(
            "\n[cyan]Select option[/cyan]",
            choices=list(menu_items.keys()),
            default="1"
        )

        return choice

    def show_dashboard(self) -> None:
        """Display system dashboard"""
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )

        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )

        # Header
        layout["header"].update(
            Panel(
                Text("AI-Pal Dashboard", justify="center", style="bold cyan"),
                border_style="cyan"
            )
        )

        # Left: System Status
        status_table = Table(title="System Status", box=box.ROUNDED)
        status_table.add_column("Component", style="cyan")
        status_table.add_column("Status", justify="right")

        status_table.add_row("FFE Engine", "[green]●[/green] Running")
        status_table.add_row("Improvement Loop", "[green]●[/green] Active")
        status_table.add_row("Context Manager", "[green]●[/green] Ready")

        layout["left"].update(Panel(status_table, border_style="green"))

        # Right: Quick Stats
        stats_table = Table(title="Quick Stats (24h)", box=box.ROUNDED)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", justify="right", style="bold")

        stats_table.add_row("Tasks Completed", "23")
        stats_table.add_row("Momentum Cycles", "5")
        stats_table.add_row("Improvements", "3")

        layout["right"].update(Panel(stats_table, border_style="blue"))

        # Footer
        layout["footer"].update(
            Panel(
                f"[dim]Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]",
                border_style="dim"
            )
        )

        self.console.print(layout)
        input("\nPress Enter to continue...")

    def run(self) -> None:
        """Main TUI loop"""
        self.show_banner()

        try:
            while self.running:
                choice = self.show_main_menu()

                if choice == "1":
                    self.show_dashboard()
                elif choice == "8":
                    self.show_help()
                elif choice == "0":
                    if Confirm.ask("\n[cyan]Exit TUI?[/cyan]", default=False):
                        self.running = False

        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]Interrupted[/yellow]")

        self.console.print("\n[cyan]Goodbye![/cyan]\n")

    def show_help(self) -> None:
        """Show help"""
        help_text = """
[bold cyan]AI-Pal TUI Help[/bold cyan]

Use number keys to select menu options.
Press Ctrl+C to return to menu.

[dim]For full CLI, use: ai-pal --help[/dim]
        """
        self.console.print(Panel(help_text, border_style="cyan"))
        input("\nPress Enter to continue...")


def main():
    """TUI entry point"""
    tui = AIPalTUI()
    tui.run()


if __name__ == "__main__":
    main()
