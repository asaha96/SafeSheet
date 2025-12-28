"""Command-line interface for SafeSheet."""

import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel

from safesheet.safety_report import SafetyReport, analyze_sql

app = typer.Typer(help="SafeSheet - Prevent accidental data loss with SQL safety analysis")
console = Console()


@app.command()
def analyze(
    sql_file: Optional[Path] = typer.Argument(None, help="Path to SQL file"),
    sql: Optional[str] = typer.Option(None, "--sql", "-s", help="SQL statement as string"),
    no_rollback: bool = typer.Option(False, "--no-rollback", help="Skip rollback generation"),
    no_dry_run: bool = typer.Option(False, "--no-dry-run", help="Skip dry-run simulation"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Analyze SQL and generate safety report."""
    # Get SQL input
    sql_text = None
    
    if sql_file:
        if not sql_file.exists():
            console.print(f"[red]Error: File not found: {sql_file}[/red]")
            raise typer.Exit(1)
        sql_text = sql_file.read_text()
    elif sql:
        sql_text = sql
    else:
        # Read from stdin
        sql_text = sys.stdin.read()
    
    if not sql_text or not sql_text.strip():
        console.print("[red]Error: No SQL provided[/red]")
        raise typer.Exit(1)
    
    # Generate report
    try:
        report_generator = SafetyReport(
            sql=sql_text,
            include_rollback=not no_rollback,
            include_dry_run=not no_dry_run,
        )
        
        report = report_generator.generate()
        formatted_report = report_generator.format_report(report)
        
        # Output report
        if output:
            output.write_text(formatted_report)
            console.print(f"[green]Report saved to: {output}[/green]")
        else:
            console.print(formatted_report)
            
            # Also print rollback script in a code block if available
            if report.get("rollback_script") and not report.get("rollback_error"):
                console.print("\n")
                console.print(Panel(
                    Syntax(report["rollback_script"], "sql", theme="monokai"),
                    title="Rollback Script",
                    border_style="yellow"
                ))
    
    except Exception as e:
        console.print(f"[red]Error analyzing SQL: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def dry_run(
    sql_file: Optional[Path] = typer.Argument(None, help="Path to SQL file"),
    sql: Optional[str] = typer.Option(None, "--sql", "-s", help="SQL statement as string"),
):
    """Run dry-run simulation of SQL statement."""
    # Get SQL input
    sql_text = None
    
    if sql_file:
        if not sql_file.exists():
            console.print(f"[red]Error: File not found: {sql_file}[/red]")
            raise typer.Exit(1)
        sql_text = sql_file.read_text()
    elif sql:
        sql_text = sql
    else:
        sql_text = sys.stdin.read()
    
    if not sql_text or not sql_text.strip():
        console.print("[red]Error: No SQL provided[/red]")
        raise typer.Exit(1)
    
    # Run dry-run
    try:
        from safesheet.parser import SQLParser
        from safesheet.dry_run import DryRunEngine
        
        parser = SQLParser(sql_text)
        dry_run_engine = DryRunEngine(parser)
        
        result = dry_run_engine.simulate(sql_text)
        
        console.print("\n[bold]Dry Run Results:[/bold]")
        console.print(f"  Simulation Successful: {'✅' if result['simulation_successful'] else '❌'}")
        console.print(f"  Statement Type: {result['statement_type']}")
        console.print(f"  Affected Tables: {', '.join(result['affected_tables']) if result['affected_tables'] else 'None'}")
        
        if result.get("estimated_rows_affected") is not None:
            console.print(f"  Estimated Rows Affected: {result['estimated_rows_affected']}")
        
        if result.get("error"):
            console.print(f"  [red]Error: {result['error']}[/red]")
        
        if result.get("preview"):
            console.print("\n  Preview:")
            for row in result["preview"][:5]:
                console.print(f"    {row}")
        
        dry_run_engine.close()
    
    except Exception as e:
        console.print(f"[red]Error running dry-run: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def report(
    sql_file: Optional[Path] = typer.Argument(None, help="Path to SQL file"),
    sql: Optional[str] = typer.Option(None, "--sql", "-s", help="SQL statement as string"),
    format: str = typer.Option("text", "--format", "-f", help="Output format: text, json"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Generate comprehensive safety report (alias for analyze)."""
    analyze(
        sql_file=sql_file,
        sql=sql,
        output=output,
    )


if __name__ == "__main__":
    app()

