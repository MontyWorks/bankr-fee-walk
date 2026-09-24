# Worked example: $QUILL

Walked 2026-09-24 with `fee_walk.py` against Robinhood Chain (chain id 4663),
RPC `https://rpc.mainnet.chain.robinhood.com`.

Command:

```text
python3 fee_walk.py 0xeC73144316ecd302AcBF197aaa6C9840803DAba3 --chain 4663
```

## Verified onchain

- Contract `0xeC73144316ecd302AcBF197aaa6C9840803DAba3` holds **44 bytes** of
  deployed bytecode: a Bankr minimal proxy, not a full token contract.
- The proxy's bytecode was scanned for embedded addresses holding code; the
  implementation it points at is
  `0x3be8b97fd0e713b5abe0649fa830223b6b4bc599` (found by the scan, not
  assumed).
- `name()` returns `QUILL`; `symbol()` returns `QUILL`; `decimals()` returns
  18. All three read clean through the proxy.
- `totalSupply()` returns 100,000,000,000 (100 billion), matching the standard
  Bankr launch supply in the docs.

## Fee schedule applied

The documented Bankr schedule (total 1.75% of volume: 0.665% claimable
creator share, 0.285% locked compounding LP share, 0.475% Bankr protocol,
0.2375% BNKR buyback, ~0.0875% Doppler) is the schedule this token launched
under. Whether its creator fees are quote-only or mixed, and who the fee
recipient is, were set at launch and are not readable from these calls.

## Explicitly NOT walked

- Pool liquidity and depth were not read. No statement is made here about how
  much liquidity the pool holds.
- Live fee accrual, claims, and the fee recipient address were not read.
- Nothing here is a statement about the token's price, safety, or legitimacy.
