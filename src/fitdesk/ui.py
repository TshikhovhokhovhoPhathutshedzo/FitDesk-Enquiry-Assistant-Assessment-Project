from rich.console import Console
from rich.panel import Panel

console = Console()


def show_customer_message(message: str) -> None:
    console.print(Panel.fit(message, title="Customer message", style="cyan"))


def show_understood_analysis(analysis) -> None:
    payload = {
        "intent": analysis.intent,
        "details": analysis.details,
        "requires_human_approval": analysis.requires_human_approval,
        "packages": analysis.packages,
        "saturday_times": analysis.saturday_times,
    }
    console.print(Panel.fit(str(payload), title="Understood as", style="magenta"))


def show_draft_reply(text: str) -> None:
    console.print(Panel.fit(text, title="Draft reply", style="green"))


def show_error(message: str) -> None:
    console.print(Panel.fit(message, title="Not sent", style="red"))
