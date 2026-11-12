from rich.console import Console


class ApprovalCancelled(Exception):
    pass


def get_staff_decision() -> str:
    console = Console()
    while True:
        try:
            response = input("Send? (y/n) ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            console.print("Cancelled by user.")
            raise ApprovalCancelled

        if response in {"y", "n"}:
            return response

        console.print("Please answer y or n.", style="yellow")
