# BTC race bot (Python 3.13, standard library only): dip-buy mean reversion on cbBTC.
# Buys a deep dip below the 2-hour high, takes a small profit, cuts losers fast,
# then waits before the next dip. Long only, one position, full cash per trade.
# Protocol: agent-fun/bars-replay/v1, via the vendored makefun_bars shim.
# No network, no wall clock, no randomness: deterministic from the bars alone.

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
LOOKBACK = 120          # bars of the 2-hour high the dip is measured from
DIP_BPS = 150           # buy when the close is 1.5% below the 2-hour high
TP_BPS = 70             # take profit 0.7% above the entry close
SL_BPS = 80             # stop loss 0.8% below the entry close
COOLDOWN = 60           # bars to wait after an exit before buying again
MAX_SLIPPAGE_BPS = 100  # 1% past the close the order was decided on

closes = []             # closes seen so far, oldest first
entry_close = None      # close at the bar the current position was decided on
last_exit_seq = -10 ** 9


def on_batch(state, batch):
    global entry_close, last_exit_seq
    for bar in batch["bars"]:
        if bar["symbol"] == SYMBOL:
            closes.append(int(bar["c"]))
    if state.warming_up:
        return []
    if len(closes) < LOOKBACK:
        return []
    held = state.positions.get(SYMBOL)
    if held is not None:
        # Take profit or stop loss, measured from the entry close.
        # Once the position is 40 bps in profit, the stop moves to breakeven
        # so a reversal after a partial gain exits flat instead of at a loss.
        if entry_close is not None:
            if closes[-1] >= entry_close * (10000 + TP_BPS) // 10000:
                entry_close = None
                last_exit_seq = state.seq
                return [{"side": "sell", "symbol": SYMBOL, "qty": held.qty,
                         "max_slippage_bps": MAX_SLIPPAGE_BPS}]
            stop = entry_close * (10000 - SL_BPS) // 10000
            if closes[-1] >= entry_close * (10000 + 40) // 10000:
                stop = entry_close
            if closes[-1] <= stop:
                entry_close = None
                last_exit_seq = state.seq
                return [{"side": "sell", "symbol": SYMBOL, "qty": held.qty,
                         "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        return []
    if state.seq - last_exit_seq < COOLDOWN:
        return []
    high = max(closes[-LOOKBACK:])
    if closes[-1] <= high * (10000 - DIP_BPS) // 10000:
        if state.cash <= 0:
            return []
        entry_close = closes[-1]
        return [{"side": "buy", "symbol": SYMBOL,
                 "notional_quote_units": state.cash,
                 "max_slippage_bps": MAX_SLIPPAGE_BPS}]
    return []


makefun_bars.run(on_batch)
