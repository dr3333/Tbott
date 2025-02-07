from typing import Literal

TradeDirection = Literal['bull', 'bear', 'both']

class TokenConfig:
    def __init__(
        self,
        name: str,
        mint_address: str,
        profit_pct: float,
        stop_purchase_above: float,
        avg_purchase_amount: float,
        max_concurrent_trades: int,
        direction: TradeDirection,
        cooldown_minutes: int,
    ):
        self.name = name
        self.mint_address = mint_address
        self.profit_pct = profit_pct
        self.stop_purchase_above = stop_purchase_above
        self.avg_purchase_amount = avg_purchase_amount
        self.max_concurrent_trades = max_concurrent_trades
        self.direction = direction
        self.cooldown_minutes = cooldown_minutes

# Example Token Configurations
TOKEN_SETTINGS = [
    TokenConfig(
        name="SOL",
        mint_address="So11111111111111111111111111111111111111112",
        profit_pct=2.5,
        stop_purchase_above=200.0,
        avg_purchase_amount=1.0,  # 1 SOL per trade
        max_concurrent_trades=3,
        direction='both',
        cooldown_minutes=15,
    ),
    # Add more tokens here
]