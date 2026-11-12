from rich.console import Console


def get_staff_decision() -> str:
    console = Console()
    while True:
        try:
            response = input("Send? (y/n) ").strip().lower()
        except KeyboardInterrupt:
            console.print("Cancelled by user.")
            return "n"

        if response in {"y", "n"}:
            return response

        console.print("Please answer y or n.", style="yellow")
