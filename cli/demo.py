import typer
from rich.console import Console
from rich.table import Table

from src.pipeline import run_pipeline

cli = typer.Typer()
console = Console()


@cli.command()
def recommend(query: str) -> None:
    result = run_pipeline(query)
    if result.refused:
        console.print(f"[red]Refused:[/red] {result.refusal_reason}")
        if result.refusal_reason_ar:
            console.print(f"[red]رفض:[/red] {result.refusal_reason_ar}")
        return

    table = Table(title="Gift Recommendations")
    table.add_column("Product", style="cyan")
    table.add_column("Price (AED)", style="green")
    table.add_column("Match Score", style="magenta")
    table.add_column("Reason", style="white")

    for item in result.recommendations:
        table.add_row(
            f"{item.name_en}\n{item.name_ar}",
            str(item.price_aed),
            f"{item.match_score:.2f}",
            f"{item.reason_en}\n{item.reason_ar}",
        )

    console.print(table)
    console.print(f"[bold]Summary:[/bold] {result.summary_en}")
    console.print(f"[bold]ملخص:[/bold] {result.summary_ar}")
    console.print(f"[bold]Confidence:[/bold] {result.confidence:.2f}")


@cli.command()
def interactive() -> None:
    console.print("[bold green]Mumzworld AI Gift Finder[/bold green]")
    console.print("Type your query (or 'quit' to exit):\n")
    while True:
        query = typer.prompt("Query")
        if query.lower() in ("quit", "exit", "q"):
            break
        recommend.callback(query)


if __name__ == "__main__":
    cli()
