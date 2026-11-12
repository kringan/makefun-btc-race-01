# BTC race bot: dip-buy mean reversion on cbBTC

A bot for make.fun's `btc-race-24h-20261112-1439` (race a BTC trading bot live
for 24 hours). It trades Coinbase Wrapped BTC (cbBTC) against USDC, minute by
minute, long only, starting from $1,000 of paper money.

## Strategy

Dip-buy mean reversion:

- Track the highest close of the last 120 one-minute bars (2 hours).
- Buy with the full cash balance when the latest close is 1.5% (150 bps)
  below that high.
- Take profit at +0.7% above the entry close; stop loss at -0.8%.
- Once the position is +0.4% in profit, the stop moves to breakeven, so a
  reversal after a partial gain exits flat instead of at a loss.
- After any exit, wait 60 bars before buying again.

One open position at most, at most one order per reply, max slippage 1% past
the close the order was decided on.

## Results (dev window, local replay)

- Net PnL: **+$4.28** on $1,000 (dev gate: PnL > 0, pass)
- Trades: 4, max drawdown 0.39%

## Layout

- `main.py` — the bot (Python 3.13, standard library only).
- `vendor/makefun_bars.py` — byte-identical copy of the kit's
  `sdk/makefun_bars.py` shim (agent-fun/bars-replay/v1).

No network, no wall clock, no randomness: deterministic from the bars alone.
