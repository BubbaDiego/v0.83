"""Service to fetch on-chain wallet balances."""

from __future__ import annotations

from typing import Optional

try:
    from web3 import Web3
except Exception:  # pragma: no cover - optional dependency
    Web3 = None  # type: ignore

try:
    from solana.rpc.api import Client
    from solana.rpc.commitment import Confirmed
    from solders.pubkey import Pubkey
except Exception as e:  # pragma: no cover - optional dependency
    import sys
    print("❌ Failed to import solana/solders:", e, file=sys.stderr)
    Client = None  # type: ignore
    Confirmed = None  # type: ignore
    Pubkey = object  # type: ignore

from core.logging import log

LAMPORTS_PER_SOL = 1_000_000_000


class CheckWalletBalanceService:
    """Simple blockchain balance checker supporting Ethereum and Solana."""

    def __init__(self,
                 eth_rpc_url: str | None = None,
                 sol_rpc_url: str | None = None) -> None:
        self.eth_rpc_url = eth_rpc_url or "https://cloudflare-eth.com"
        self.sol_rpc_url = sol_rpc_url or "https://api.mainnet-beta.solana.com"
        self._eth = Web3(Web3.HTTPProvider(self.eth_rpc_url)) if Web3 else None
        self._sol = Client(self.sol_rpc_url) if Client else None
        log.debug(
            f"CheckWalletBalanceService initialized", source="WalletBalanceSvc"
        )

    def get_balance(self, address: str) -> Optional[float]:
        """Return balance for ``address`` in native units or ``None`` on error."""
        if address.startswith("0x"):
            # Ethereum style
            if not self._eth:
                log.error("web3 library unavailable", source="WalletBalanceSvc")
                return None
            try:
                wei = self._eth.eth.get_balance(address)
                return float(self._eth.from_wei(wei, "ether"))
            except Exception as exc:
                log.error(
                    f"ETH balance fetch failed for {address}: {exc}",
                    source="WalletBalanceSvc",
                )
                return None
        # Default to Solana
        if not self._sol:
            log.error("solana library unavailable", source="WalletBalanceSvc")
            return None
        try:
            kwargs = {}
            if Confirmed:
                kwargs["commitment"] = Confirmed
            clean_address = address.strip()
            resp = self._sol.get_balance(Pubkey.from_string(clean_address), **kwargs)
            lamports = resp.value
            if lamports is not None:
                return lamports / LAMPORTS_PER_SOL
        except Exception as exc:
            log.error(
                f"SOL balance fetch failed for {address}: {exc}",
                source="WalletBalanceSvc",
            )
        return None
