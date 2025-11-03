"""
AI-PAL Command Line Interface

Interactive CLI for the AI-PAL cognitive partner system.

Features:
- Start and manage goals
- Momentum Loop interaction
- ARI score tracking
- Personality discovery
- Social features (win sharing, groups)
- Teaching mode
"""

import asyncio
from pathlib import Path
from typing import Optional
from datetime import datetime

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich import print as rprint

from .core.integrated_system import IntegratedACSystem, SystemConfig

# Initialize Typer app
app = typer.Typer(
    name="ai-pal",
    help="AI-PAL: Privacy-first AC-AI cognitive partner",
    add_completion=False,
)

# Rich console for beautiful output
console = Console()

# Global system instance
_system: Optional[IntegratedACSystem] = None


def get_system() -> IntegratedACSystem:
    """Get or initialize the AC system"""
    global _system
    if _system is None:
        data_dir = Path.home() / ".ai-pal" / "data"
        credentials_path = Path.home() / ".ai-pal" / "credentials.json"

        config = SystemConfig(
            data_dir=data_dir,
            credentials_path=credentials_path,
            enable_gates=True,
            enable_tribunal=True,
            enable_ari_monitoring=True,
            enable_edm_monitoring=True,
            enable_self_improvement=True,
            enable_privacy_protection=True,
            enable_context_management=True,
            enable_model_orchestration=True,
            enable_dashboard=True,
            enable_ffe=True,
            enable_social_features=True,
            enable_personality_discovery=True,
            enable_teaching_mode=True,
        )

        console.print("[dim]Initializing AI-PAL system...[/dim]")
        _system = IntegratedACSystem(config=config)
        console.print("[green]✓[/green] AI-PAL ready!")

    return _system


def get_user_id() -> str:
    """Get current user ID (from config or environment)"""
    # In production, would come from auth
    return "default_user"


# ===== MAIN COMMANDS =====


@app.command()
def status():
    """Show system status and user's current state"""
    system = get_system()
    user_id = get_user_id()

    console.print(Panel.fit(
        "[bold cyan]AI-PAL System Status[/bold cyan]",
        border_style="cyan"
    ))

    # System health
    console.print("\n[bold]System Health:[/bold]")
    console.print("  ✓ All systems operational")

    # User stats
    if system.ari_monitor:
        console.print("\n[bold]Your Agency Score:[/bold]")
        try:
            summary = system.ari_monitor.get_user_summary(user_id)
            if summary and 'snapshot_count' in summary and summary['snapshot_count'] > 0:
                # Have ARI data
                console.print(f"  Snapshots recorded: {summary['snapshot_count']}")
                console.print("  [dim]Use 'ai-pal ari' for detailed history[/dim]")
            else:
                console.print("  [dim]No data yet. Start using AI-PAL to track your autonomy![/dim]")
        except Exception as e:
            console.print(f"  [dim]ARI tracking ready[/dim]")

    # FFE stats
    if system.ffe_engine:
        console.print("\n[bold]Your Goals:[/bold]")
        console.print("  Active goals: 0")  # Would query actual goals
        console.print("  Completed this week: 0")

    console.print()


@app.command()
def start(
    goal: Optional[str] = typer.Argument(None, help="Goal description")
):
    """Start a new goal"""
    system = get_system()
    user_id = get_user_id()

    if not system.ffe_engine:
        console.print("[red]✗[/red] FFE not available")
        raise typer.Exit(1)

    # Get goal from user if not provided
    if not goal:
        console.print(Panel.fit(
            "[bold cyan]What do you want to accomplish?[/bold cyan]",
            border_style="cyan"
        ))
        goal = Prompt.ask("\n[bold]Goal[/bold]")

    console.print(f"\n[dim]Starting goal: {goal}[/dim]\n")

    # Start goal
    async def _start():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing goal...", total=None)

            goal_packet = await system.ffe_engine.start_goal(
                user_id=user_id,
                goal_description=goal
            )

            progress.update(task, description="Breaking down into steps...")

            blocks = await system.ffe_engine.break_down_goal(goal_packet)

            progress.stop()

            # Show goal breakdown
            console.print(Panel.fit(
                f"[bold green]Goal Value: {goal_packet.estimated_value:.0%}[/bold green]\n"
                f"[dim]Effort Required: {goal_packet.estimated_effort:.0%}[/dim]",
                title="Goal Analysis",
                border_style="green"
            ))

            # Show blocks
            table = Table(title="Action Plan (5-Block Stop Rule)")
            table.add_column("#", style="cyan", width=4)
            table.add_column("Block", style="white")
            table.add_column("Duration", justify="right", style="green")

            for i, block in enumerate(blocks[:5], 1):
                table.add_row(
                    str(i),
                    block.title,
                    f"{block.time_block_size.value}min"
                )

            console.print(table)
            console.print(f"\n[bold]Goal ID:[/bold] {goal_packet.goal_id}")

            # Ask if they want to start
            if Confirm.ask("\nStart first block?"):
                # Start momentum loop
                loop_state = await system.ffe_engine.start_momentum_loop(
                    user_id=user_id,
                    atomic_block=blocks[0]
                )

                console.print(Panel.fit(
                    f"[bold cyan]Block 1 Started![/bold cyan]\n\n"
                    f"{blocks[0].strength_reframe or blocks[0].description}\n\n"
                    f"[dim]Momentum Loop: {loop_state.current_state.value}[/dim]",
                    border_style="cyan"
                ))

    asyncio.run(_start())


@app.command()
def complete(
    goal_id: str = typer.Argument(..., help="Goal ID")
):
    """Mark current block as complete"""
    console.print(f"[green]✓[/green] Block completed!")
    console.print("\n[bold]How did it go?[/bold]")

    quality = Prompt.ask(
        "Quality (1-10)",
        default="8"
    )

    console.print(Panel.fit(
        "[bold green]WIN![/bold green]\n\n"
        f"Quality: {quality}/10\n"
        "You're building momentum! 🎯",
        border_style="green"
    ))


@app.command()
def ari():
    """View your ARI (Autonomy Retention Index) history"""
    system = get_system()
    user_id = get_user_id()

    if not system.ari_monitor:
        console.print("[red]✗[/red] ARI monitoring not available")
        raise typer.Exit(1)

    console.print(Panel.fit(
        "[bold cyan]Your Autonomy Retention Index[/bold cyan]",
        border_style="cyan"
    ))

    # Get user summary
    try:
        summary = system.ari_monitor.get_user_summary(user_id)

        if not summary or summary.get('snapshot_count', 0) == 0:
            console.print("\n[yellow]No ARI data yet. Start using AI-PAL to build your history![/yellow]")
            return

        # Show summary
        console.print("\n[bold]Summary:[/bold]")
        console.print(f"  Total snapshots: {summary.get('snapshot_count', 0)}")

        if 'latest_score' in summary:
            score = summary['latest_score']
            if score >= 0.7:
                color = "green"
            elif score >= 0.5:
                color = "yellow"
            else:
                color = "red"
            console.print(f"  Latest ARI: [{color}]{score:.2%}[/{color}]")

        console.print("\n[dim]ARI tracking is active. Continue using AI-PAL to see your autonomy trends.[/dim]")

    except Exception as e:
        console.print(f"\n[yellow]Error retrieving ARI history: {e}[/yellow]")
        console.print("[dim]Try interacting with AI-PAL to generate data.[/dim]")


# ===== PERSONALITY COMMANDS =====

personality_app = typer.Typer(help="Personality discovery and insights")
app.add_typer(personality_app, name="personality")


@personality_app.command("discover")
def personality_discover():
    """Start personality discovery session"""
    system = get_system()
    user_id = get_user_id()

    if not system.ffe_engine or not system.ffe_engine.personality_discovery:
        console.print("[red]✗[/red] Personality discovery not available")
        raise typer.Exit(1)

    console.print(Panel.fit(
        "[bold cyan]Discover Your Signature Strengths[/bold cyan]\n\n"
        "Answer a few questions to identify what makes you unique.",
        border_style="cyan"
    ))

    async def _discover():
        # Start session
        session = await system.ffe_engine.personality_discovery.start_discovery_session(user_id)

        questions_answered = 0
        max_questions = 10

        while questions_answered < max_questions:
            # Get next question
            question = await system.ffe_engine.personality_discovery.get_next_question(
                session.session_id
            )

            if not question:
                break

            # Show question
            console.print(f"\n[bold cyan]Question {questions_answered + 1}/{max_questions}[/bold cyan]")
            console.print(f"\n{question.question_text}\n")

            # Get answer based on type
            if question.question_type.value == "multiple_choice":
                for i, option in enumerate(question.options, 1):
                    console.print(f"  {i}. {option['text']}")

                choice = Prompt.ask(
                    "\nYour choice",
                    choices=[str(i) for i in range(1, len(question.options) + 1)]
                )
                answer = int(choice) - 1

            elif question.question_type.value == "open_ended":
                answer = Prompt.ask("Your answer")

            else:
                # Ranking or other types
                answer = Prompt.ask("Your answer")

            # Record answer
            await system.ffe_engine.personality_discovery.record_answer(
                session.session_id,
                question.question_id,
                answer
            )

            questions_answered += 1

        # Complete session
        result = await system.ffe_engine.personality_discovery.complete_session(
            session.session_id,
            user_id
        )

        # Show results
        console.print(Panel.fit(
            "[bold green]Discovery Complete![/bold green]",
            border_style="green"
        ))

        console.print(f"\n[bold]Your Signature Strengths:[/bold]\n")

        for strength in result.get("strengths", []):
            confidence = strength.confidence_score
            if confidence >= 0.7:
                badge = "🌟"
            elif confidence >= 0.5:
                badge = "✨"
            else:
                badge = "💫"

            console.print(
                f"{badge} [bold]{strength.identity_label}[/bold] "
                f"({confidence:.0%} confidence)\n"
                f"   [dim]{strength.strength_description}[/dim]\n"
            )

    asyncio.run(_discover())


@personality_app.command("show")
def personality_show():
    """Show your current strengths"""
    system = get_system()
    user_id = get_user_id()

    if not system.ffe_engine or not system.ffe_engine.personality_connector:
        console.print("[red]✗[/red] Personality features not available")
        raise typer.Exit(1)

    async def _show():
        strengths = await system.ffe_engine.personality_connector.get_current_strengths(user_id)

        if not strengths:
            console.print("\n[yellow]No strengths discovered yet.[/yellow]")
            console.print("Run [cyan]ai-pal personality discover[/cyan] to get started!")
            return

        table = Table(title="Your Signature Strengths")
        table.add_column("Strength", style="cyan")
        table.add_column("Confidence", justify="right", style="green")
        table.add_column("Examples", style="dim")

        for s in strengths:
            examples = ", ".join(s.demonstrated_examples[-2:]) if s.demonstrated_examples else "None yet"
            table.add_row(
                s.identity_label,
                f"{s.confidence_score:.0%}",
                examples[:50] + "..." if len(examples) > 50 else examples
            )

        console.print(table)

    asyncio.run(_show())


# ===== SOCIAL COMMANDS =====

social_app = typer.Typer(help="Social features - win sharing and groups")
app.add_typer(social_app, name="social")


@social_app.command("groups")
def social_groups():
    """List your groups"""
    system = get_system()
    user_id = get_user_id()

    if not system.ffe_engine or not system.ffe_engine.social_interface:
        console.print("[red]✗[/red] Social features not available")
        raise typer.Exit(1)

    async def _list():
        groups = await system.ffe_engine.social_interface.list_my_groups(user_id)

        if not groups:
            console.print("\n[yellow]You're not in any groups yet.[/yellow]")
            console.print("Create one with: [cyan]ai-pal social create-group[/cyan]")
            return

        table = Table(title="Your Groups")
        table.add_column("Group", style="cyan")
        table.add_column("Members", justify="right", style="white")
        table.add_column("Wins Shared", justify="right", style="green")

        for g in groups:
            table.add_row(
                g["name"],
                str(g["member_count"]),
                str(g["total_wins_shared"])
            )

        console.print(table)

    asyncio.run(_list())


@social_app.command("create-group")
def social_create_group(
    name: str = typer.Argument(..., help="Group name"),
    description: str = typer.Option(..., "--description", "-d", help="Group description"),
    open_group: bool = typer.Option(False, "--open", help="Anyone can join")
):
    """Create a new sharing group"""
    system = get_system()
    user_id = get_user_id()

    if not system.ffe_engine or not system.ffe_engine.social_interface:
        console.print("[red]✗[/red] Social features not available")
        raise typer.Exit(1)

    async def _create():
        result = await system.ffe_engine.social_interface.create_group(
            user_id=user_id,
            name=name,
            description=description,
            is_open=open_group
        )

        console.print(Panel.fit(
            f"[bold green]Group Created![/bold green]\n\n"
            f"Name: {result['name']}\n"
            f"ID: {result['group_id']}\n"
            f"Type: {'Open' if open_group else 'Invite-only'}",
            border_style="green"
        ))

    asyncio.run(_create())


# ===== TEACHING COMMANDS =====

teach_app = typer.Typer(help="Teaching mode - become a protégé")
app.add_typer(teach_app, name="teach")


@teach_app.command("start")
def teach_start():
    """Start teaching AI-PAL about your domain"""
    system = get_system()
    user_id = get_user_id()

    if not system.ffe_engine or not system.ffe_engine.teaching_interface:
        console.print("[red]✗[/red] Teaching mode not available")
        raise typer.Exit(1)

    console.print(Panel.fit(
        "[bold cyan]Teaching Mode[/bold cyan]\n\n"
        "You're the expert. Teach AI-PAL about your domain.\n"
        "Explaining concepts deepens your understanding! 🎓",
        border_style="cyan"
    ))

    async def _teach():
        result = await system.ffe_engine.teaching_interface.start_teaching_mode(user_id)

        console.print("\n[bold]What would you like to teach about?[/bold]")
        topic = Prompt.ask("Topic")

        console.print("\n[bold]Explain it in your own words:[/bold]")
        explanation = Prompt.ask("Explanation")

        # Submit teaching
        await system.ffe_engine.teaching_interface.submit_teaching_content(
            user_id=user_id,
            topic=topic,
            explanation=explanation,
            examples=[]
        )

        console.print(Panel.fit(
            f"[bold green]Excellent![/bold green]\n\n"
            f"You just taught AI-PAL about [cyan]{topic}[/cyan].\n"
            f"Teaching is one of the best ways to solidify knowledge! 🌟",
            border_style="green"
        ))

    asyncio.run(_teach())


@teach_app.command("topics")
def teach_topics():
    """View topics you've taught"""
    system = get_system()
    user_id = get_user_id()

    if not system.ffe_engine or not system.ffe_engine.teaching_interface:
        console.print("[red]✗[/red] Teaching mode not available")
        raise typer.Exit(1)

    async def _topics():
        topics = await system.ffe_engine.teaching_interface.get_taught_topics(user_id)

        if not topics:
            console.print("\n[yellow]You haven't taught any topics yet.[/yellow]")
            console.print("Start with: [cyan]ai-pal teach start[/cyan]")
            return

        console.print(Panel.fit(
            f"[bold cyan]Topics You've Taught: {len(topics)}[/bold cyan]",
            border_style="cyan"
        ))

        for topic in topics:
            console.print(f"  • {topic}")

    asyncio.run(_topics())


# ===== VERSION =====

@app.command()
def version():
    """Show AI-PAL version"""
    console.print("[bold cyan]AI-PAL[/bold cyan] v1.0.0")
    console.print("Privacy-first AC-AI cognitive partner system")


if __name__ == "__main__":
    app()
