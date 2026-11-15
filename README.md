# Files for iterativv/NostalgiaForInfinity #1546 (signal 507) and #1592 (signal 14)

Binance futures, 82 windows (78 yearly 2021–2026 plus 4 windows on 80 extra pairs, 2025-09 → 2026-09). 60 slots: stake 1,000, wallet 100,000 per window. Book: NFI `exampleconfig.json`, 6 slots, unlimited stake, wallet 10,000 per window.

| folder | head | compared |
|---|---|---|
| `1546/` | `8ae121675` | the head with signal 507 off vs on |
| `1592/` | `5a26c157d` | the head with signal 14 off vs on |

- `60_windows.csv`, `book_windows.csv`: per window, off vs on: trades, net, real losses, drawdown, liquidations, the signal's own trades and net, displaced trades, net change.
- `60_displaced_by_tag.csv`, `book_displaced_by_tag.csv`: other signals' trades pushed out (displaced) or added, per tag.
- `60_displaced_trades.csv`, `book_displaced_trades.csv`: every displaced trade (off only) and every added trade (on only).
- `parity.txt`: the head with the signal off vs `main` v18.0.248 (`e754f6980`), trade for trade (pair, open, close, tag, exit, profit).

`real loss` = `profit_abs <= 0` and not `force_exit`. Pairs on the binance blacklist are left out of the counts.
