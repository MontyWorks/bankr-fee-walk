# Worked example: $MDOG

Walked 2026-09-24 with `fee_walk.py` against Robinhood Chain (chain id 4663),
RPC `https://rpc.mainnet.chain.robinhood.com`.

Command:

```text
python3 fee_walk.py 0x4CAF2e6eC0fCBef77314566A9884643512EF8bfC --chain 4663
```

## Verified onchain

- Contract `0x4CAF2e6eC0fCBef77314566A9884643512EF8bfC` holds **3,248 bytes**
  of deployed bytecode: a full contract, not a Bankr minimal proxy.
- `name()` returns `Muse Dog`; `symbol()` returns `MDOG`; `decimals()`
  returns 18. All three read clean.
- `totalSupply()` returns **1,000,000,000 (1 billion)** — this differs from
  the standard 100-billion-token Bankr launch supply in the docs. The reason
  is not established here; the figure is reported exactly as the contract
  returns it.

## Fee schedule applied

The 1.75% documented Bankr schedule is shown for reference, but $MDOG is not
a 44-byte Bankr minimal proxy and its supply is non-standard, so the standard
launch assumptions should not be applied to it without further verification.
Quote-only vs mixed fee mode and the fee recipient are not readable from
these calls.

## Explicitly NOT walked

- Pool liquidity and depth were not read.
- The token's launch mechanism, fee configuration, and fee recipient were not
  determined.
- Nothing here is a statement about the token's price, safety, or legitimacy.
