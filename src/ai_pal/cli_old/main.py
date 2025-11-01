"""Main CLI application for AI Pal."""

import asyncio
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from loguru import logger

from ai_pal import __version__
from ai_pal.core.orchestrator import Orchestrator, OrchestratorRequest
from ai_pal.core.config import settings
from ai_pal.core.hardware import get_hardware_info

app = typer.Typer(
    name="ai-pal",
    help="AI Pal - Privacy-First Cognitive Partner",
    add_completion=False,
)

console = Console()


@app.command()
def version():
    """Show AI Pal version."""
    console.print(f"[bold cyan]AI Pal[/bold cyan] version [green]{__version__}[/green]")


@app.command()
def info():
    """Show system information and hardware capabilities."""
    console.print("\n[bold cyan]AI Pal System Information[/bold cyan]\n")

    # Version
    console.print(f"Version: [green]{__version__}[/green]")

    # Hardware
    hardware = get_hardware_info()
    console.print("\n[bold]Hardware:[/bold]")
    console.print(str(hardware))

    # Configuration
    console.print("\n[bold]Configuration:[/bold]")
    console.print(f"Local-only mode: [yellow]{settings.local_only_mode}[/yellow]")
    console.print(f"PII scrubbing: [yellow]{settings.enable_pii_scrubbing}[/yellow]")
    console.print(f"Four Gates enabled: [yellow]{settings.enable_four_gates}[/yellow]")

    # Enabled modules
    modules = settings.get_enabled_modules()
    console.print(f"\nEnabled modules: [cyan]{', '.join(modules)}[/cyan]")

    # Cloud APIs
    has_cloud = settings.has_cloud_api_keys()
    console.print(f"\nCloud API access: [yellow]{has_cloud}[/yellow]")
    if has_cloud:
        if settings.openai_api_key:
            console.print("  - OpenAI: [green]✓[/green]")
        if settings.anthropic_api_key:
            console.print("  - Anthropic: [green]✓[/green]")
        if settings.cohere_api_key:
            console.print("  - Cohere: [green]✓[/green]")


@app.command()
def init():
    """Initialize AI Pal (create directories, download models, etc.)."""
    console.print("[bold cyan]Initializing AI Pal...[/bold cyan]\n")

    # Create directories
    settings.local_models_path.mkdir(parents=True, exist_ok=True)
    settings.log_file.parent.mkdir(parents=True, exist_ok=True)

    data_dir = settings.database_url.replace("sqlite:///", "").rsplit("/", 1)[0]
    import os
    os.makedirs(data_dir, exist_ok=True)

    console.print("[green]✓[/green] Directories created")

    # Check environment
    if not settings.has_cloud_api_keys() and not settings.default_local_model:
        console.print(
            "\n[yellow]⚠[/yellow] No API keys or local model configured."
        )
        console.print(
            "To use cloud LLMs, set API keys in .env file."
        )
        console.print(
            "To use local models, download a model and set DEFAULT_LOCAL_MODEL in .env"
        )

    console.print("\n[green]✓[/green] AI Pal initialized successfully!")
    console.print(
        "\nNext steps:"
    )
    console.print("  1. Configure .env file with your preferences")
    console.print("  2. Run 'ai-pal chat' to start a conversation")
    console.print("  3. Run 'ai-pal --help' to see all commands")


@app.command()
def chat(
    user_id: Optional[str] = typer.Option(
        "default_user", "--user", "-u", help="User ID for personalization"
    ),
    local_only: bool = typer.Option(
        False, "--local-only", "-l", help="Use only local models"
    ),
):
    """Start an interactive chat session."""
    console.print(
        Panel.fit(
            "[bold cyan]AI Pal - Privacy-First Cognitive Partner[/bold cyan]\n"
            f"Version {__version__}\n\n"
            "Type 'exit' or 'quit' to end the session.",
            border_style="cyan",
        )
    )

    # Run async chat
    asyncio.run(_chat_session(user_id, local_only))


async def _chat_session(user_id: str, local_only: bool):
    """Run interactive chat session."""
    # Initialize orchestrator
    console.print("\n[dim]Initializing AI Pal...[/dim]")

    orchestrator = Orchestrator()
    await orchestrator.initialize()

    console.print("[dim green]Ready![/dim green]\n")

    # Chat loop
    while True:
        try:
            # Get user input
            user_input = console.input("\n[bold cyan]You:[/bold cyan] ")

            if user_input.lower() in ["exit", "quit", "bye"]:
                console.print("\n[dim]Goodbye! 👋[/dim]\n")
                break

            if not user_input.strip():
                continue

            # Process request
            console.print("\n[dim]Thinking...[/dim]\n")

            request = OrchestratorRequest(
                user_id=user_id,
                message=user_input,
                prefer_local=local_only or settings.local_only_mode,
            )

            response = await orchestrator.process(request)

            # Display response
            console.print(
                Panel(
                    Markdown(response.message),
                    title="[bold green]AI Pal[/bold green]",
                    border_style="green",
                )
            )

            # Display metadata in debug mode
            if settings.log_level == "DEBUG":
                console.print(
                    f"\n[dim]Model: {response.model_used} | "
                    f"Time: {response.processing_time_ms:.0f}ms | "
                    f"PII scrubbed: {response.pii_scrubbed}[/dim]"
                )

        except KeyboardInterrupt:
            console.print("\n\n[dim]Session interrupted. Goodbye! 👋[/dim]\n")
            break

        except Exception as e:
            console.print(f"\n[red]Error:[/red] {e}\n")
            logger.exception("Chat error")

    # Cleanup
    await orchestrator.shutdown()


@app.command()
def metrics(
    agency: bool = typer.Option(
        False, "--agency", "-a", help="Show agency metrics"
    ),
):
    """View system metrics and analytics."""
    console.print("[bold cyan]AI Pal Metrics[/bold cyan]\n")

    async def _show_metrics():
        orchestrator = Orchestrator()
        await orchestrator.initialize()

        if agency:
            # Show agency metrics
            dashboard = await orchestrator.get_ethics_dashboard()

            table = Table(title="Agency Metrics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            for key, value in dashboard.items():
                if isinstance(value, float):
                    table.add_row(key, f"{value:.3f}")
                else:
                    table.add_row(key, str(value))

            console.print(table)

        await orchestrator.shutdown()

    asyncio.run(_show_metrics())


@app.command()
def status():
    """Check system status and health."""
    console.print("[bold cyan]AI Pal System Status[/bold cyan]\n")

    async def _check_status():
        orchestrator = Orchestrator()
        await orchestrator.initialize()

        health = await orchestrator.health_check()

        # Display health status
        console.print("[bold]Orchestrator:[/bold]")
        status_icon = "[green]✓[/green]" if health["orchestrator_initialized"] else "[red]✗[/red]"
        console.print(f"  {status_icon} Initialized")

        console.print("\n[bold]Ethics Module:[/bold]")
        status_icon = "[green]✓[/green]" if health["ethics_module_active"] else "[red]✗[/red]"
        console.print(f"  {status_icon} Active")

        console.print("\n[bold]Modules:[/bold]")
        for name, healthy in health["modules"].items():
            status_icon = "[green]✓[/green]" if healthy else "[red]✗[/red]"
            console.print(f"  {status_icon} {name}")

        console.print("\n[bold]LLM Providers:[/bold]")
        for name, healthy in health["llm_providers"].items():
            status_icon = "[green]✓[/green]" if healthy else "[red]✗[/red]"
            console.print(f"  {status_icon} {name}")

        await orchestrator.shutdown()

    asyncio.run(_check_status())


@app.command()
def ethics_check(
    action: str = typer.Argument(..., help="Action to check against Four Gates"),
):
    """Check an action against the Four Gates."""
    console.print(
        f"[bold cyan]Running Four Gates check for:[/bold cyan] {action}\n"
    )

    async def _ethics_check():
        orchestrator = Orchestrator()
        await orchestrator.initialize()

        # Run Four Gates
        from ai_pal.modules.base import ModuleRequest
        from datetime import datetime

        request = ModuleRequest(
            task=action,
            context={},
            user_id="cli_user",
            timestamp=datetime.now(),
            metadata={},
        )

        response = await orchestrator.ethics_module.process(request)
        gates_result = response.result

        # Display results
        console.print(str(gates_result))

        await orchestrator.shutdown()

    asyncio.run(_ethics_check())


if __name__ == "__main__":
    app()
