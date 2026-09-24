# Worked example: $PORCH

Walked 2026-09-24 with `fee_walk.py` against Robinhood Chain (chain id 4663),
RPC `https://rpc.mainnet.chain.robinhood.com`.

Command:

```text
python3 fee_walk.py 0x4B434541873f171aB70D7d2F3a48b0f0b0f13ba3 --chain 4663
```

## Verified onchain

- Contract `0x4B434541873f171aB70D7d2F3a48b0f0b0f13ba3` holds **44 bytes** of
  deployed bytecode: a Bankr minimal proxy.
- Bytecode scan finds the same implementation as $QUILL:
  `0x3be8b97fd0e713b5abe0649fa830223b6b4bc599`.
- `name()` returns `Porch`; `symbol()` returns `PORCH`; `decimals()` returns
  18. All three read clean through the proxy.
- `totalSupply()` returns 100,000,000,000 (100 billion), matching the standard
  Bankr launch supply in the docs.

## Fee schedule applied

Same documented Bankr schedule as $QUILL (1.75% all-in). Quote-only vs mixed
fee mode and the fee recipient were set at launch and are not readable from
these calls.

## Explicitly NOT walked

- Pool liquidity and depth were not read.
- Live fee accrual, claims, and the fee recipient address were not read.
- Nothing here is a statement about the token's price, safety, or legitimacy.
