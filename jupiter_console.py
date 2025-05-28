"""Interactive console for Jupiter collateral testing."""

from typing import Optional
from rich.console import Console

from core.core_imports import configure_console_log, DB_PATH
from data.data_locker import DataLocker
from wallets.wallet_core import WalletCore

try:
    from solana.transaction import Transaction
    import base64
except Exception:  # pragma: no cover - optional dependency
    Transaction = None
    base64 = None

console = Console()
configure_console_log()


def _select_wallet(core: WalletCore):
    wallets = core.load_wallets()
    if not wallets:
        console.print("[red]No wallets found.[/red]")
        return None
    console.print("\nAvailable wallets:")
    for idx, w in enumerate(wallets, start=1):
        console.print(f"{idx}) {w.name} ({w.public_address})")
    try:
        choice = int(console.input("Select wallet > ").strip())
        return wallets[choice - 1]
    except Exception:
        console.print("[red]Invalid selection[/red]")
        return None


def _get_input(prompt: str, cast=float):
    try:
        return cast(console.input(prompt).strip())
    except Exception:
        console.print("[red]Invalid input[/red]")
        return None


def _maybe_send_tx(core: WalletCore, wallet, result: dict):
    msg = result.get("transaction") or result.get("message")
    if not (msg and Transaction and base64):
        console.print("[yellow]No transaction payload returned.[/yellow]")
        return
    try:
        tx = Transaction.deserialize(base64.b64decode(msg))
        sig = core.send_transaction(wallet, tx)
        console.print(f"[green]Signature:[/green] {sig}")
    except Exception as exc:
        console.print(f"[red]Failed to sign/send: {exc}[/red]")


def deposit_flow(core: WalletCore):
    wallet = _select_wallet(core)
    if not wallet:
        return
    market = console.input("Market symbol > ").strip()
    amount = _get_input("Amount > ")
    if amount is None:
        return
    result = core.deposit_collateral(wallet, market, amount)
    console.print(result)
    if result:
        _maybe_send_tx(core, wallet, result)


def withdraw_flow(core: WalletCore):
    wallet = _select_wallet(core)
    if not wallet:
        return
    market = console.input("Market symbol > ").strip()
    amount = _get_input("Amount > ")
    if amount is None:
        return
    result = core.withdraw_collateral(wallet, market, amount)
    console.print(result)
    if result:
        _maybe_send_tx(core, wallet, result)


def main():
    DataLocker.get_instance(str(DB_PATH))  # ensure DB initialized
    core = WalletCore()
    while True:
        console.print("\n[bold cyan]Jupiter Collateral Console[/bold cyan]")
        console.print("1) Deposit Collateral")
        console.print("2) Withdraw Collateral")
        console.print("3) Exit")
        choice = console.input("Choose > ").strip()
        if choice == "1":
            deposit_flow(core)
        elif choice == "2":
            withdraw_flow(core)
        elif choice == "3":
            break
        else:
            console.print("[red]Invalid choice[/red]")


if __name__ == "__main__":
    main()
