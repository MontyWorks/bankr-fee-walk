# bankr-fee-walk

A small toolkit that re-derives a Bankr-launched token's expected fee split
from onchain reads, so a stranger can verify the fee math themselves.

It reads `name`, `symbol`, `decimals`, and `totalSupply` directly from the
token contract over JSON-RPC, classifies the contract as a Bankr minimal proxy
or a full contract from its deployed bytecode, and prints the documented
Bankr fee schedule with the arithmetic shown. Python standard library only.
No dependencies, no API keys.

This is a reading tool. It is not financial advice, it makes no statement
about any token's price or safety, and it is not affiliated with Bankr.

## The Bankr fee model (as documented)

Every figure below was verified 2026-09-24 against the official Bankr
documentation: `https://docs.bankr.bot/llms-full.txt` ("Fee Structure" and
"Token Supply" sections). The docs are the authority; if they change, this
file is stale.

### Swap fee: 1.75% of trading volume, all-in

| Recipient | Share of volume | Derivation |
| --- | --- | --- |
| Creator (claimable) — 95% of the 0.7% pool swap fee, paid directly, claim anytime | 0.665% | 0.95 x 0.70% |
| LP fee (via hook) — auto-compounds as permanently locked pool liquidity | 0.285% | documented |
| Bankr protocol fee (via hook) | 0.475% | documented |
| BNKR buyback (via hook) — buybacks + protocol-owned BNKR liquidity | 0.2375% | documented |
| Protocol / Doppler (via hook) | ~0.0875% | documented (approximate) |
| **Total** | **1.75%** | 0.665 + 0.285 + 0.475 + 0.2375 + 0.0875 |

The creator side totals 0.95% of volume, but only the 0.665% is claimable
fee revenue; the 0.285% LP share compounds as locked pool liquidity and is
not spendable. Fee schedules are fixed at launch and never change
retroactively — the docs note that existing tokens keep the schedule they
launched with, and the split above applies to new launches.

### Quote-only vs mixed fees

By default, creator fees accrue as a mix of the launched token and the quote
token. At launch the creator can instead opt into **quote-only fees**, so all
creator fees are collected in the quote token; the docs state the total take
is identical either way. Like the fee schedule itself, this choice is fixed
at launch.

### Supply and vesting

Standard Bankr launches use a fixed, non-mintable supply of **100 billion
tokens**: **85%** seeds the Uniswap V4 liquidity pool and **15%** is preminted
to the fee recipient, vesting over **1 year** with a **30-day cliff** (the
cliff sits inside the one-year window, not on top of it). The vesting
recipient is locked at launch and cannot be reassigned; transferring fee
rights later does not move the vested allocation. Vesting can be turned off
at launch, in which case 100% of supply goes to the pool.

## Usage

```text
python3 fee_walk.py <token-address> --chain 4663
```

Options: `--chain` (default 4663, Robinhood Chain; 8453 Base is also mapped),
`--rpc` to override the endpoint, `--volume` to set the sample USD volume
used in the worked math (default 10,000).

The script tries its built-in public RPC list in order and uses the first one
that answers with the expected chain id. On 2026-09-24 the working endpoint
for Robinhood Chain was `https://rpc.mainnet.chain.robinhood.com`
(`https://rpc.robinhoodchain.io` did not answer; `https://lb.routeme.sh/rpc/evm/4663`
was rate-limited).

For a 44-byte contract the script scans the bytecode for an embedded address
that holds code and reports it as the proxy implementation — the address is
found, not assumed.

## Worked examples

The `worked-examples/` directory holds three real cold-walks performed
2026-09-24 on Robinhood Chain: $QUILL and $PORCH (both 44-byte Bankr minimal
proxies pointing at the same implementation) and $MDOG (a full 3,248-byte
contract with a non-standard 1B supply). Each file records exactly what was
verified onchain and explicitly states what was not walked (liquidity and
depth were never read).

## Limits

- The script shows the *documented* fee schedule, not live fee state. It does
  not read fee accrual, claims, recipients, or pool reserves.
- Quote-only vs mixed fee mode and the actual fee recipient are set at launch
  and are not readable from these calls.
- Figures were verified against the Bankr docs on 2026-09-24. If the docs
  change, re-verify before relying on them.
