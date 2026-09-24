#!/usr/bin/env python3
"""bankr-fee-walk: re-derive a Bankr-launched token's expected fee split from onchain reads.

Reads name, symbol, decimals and totalSupply directly from the token contract
via JSON-RPC, classifies the contract as a Bankr minimal proxy or a full
contract from its deployed bytecode, and prints the documented Bankr fee split
with the arithmetic shown.

Python standard library only (urllib). No dependencies, no API keys.

Usage:
    python3 fee_walk.py 0xeC73144316ecd302AcBF197aaa6C9840803DAba3 --chain 4663
    python3 fee_walk.py <token-address> --chain 8453 --rpc https://mainnet.base.org

What this does NOT do: it does not read pool liquidity, fee accrual, or any
price. It prints the *documented* fee schedule, not live fee state. It is a
reading tool, not financial advice, and it is not affiliated with Bankr.
"""

import argparse
import json
import sys
import urllib.request
import urllib.error

# Fee schedule verified 2026-09-24 against the official Bankr documentation at
# https://docs.bankr.bot/llms-full.txt ("Fee Structure" and "Token Supply"
# sections). All figures are shares of trading volume. The schedule is fixed
# at launch and never changes retroactively (docs: "Existing tokens are
# unaffected" note).
FEE_ROWS = [
    # (label, derivation, share_of_volume)
    ("Creator (claimable) - 95% of the 0.7% pool swap fee",
     "0.95 x 0.70%", 0.00665),
    ("LP fee (hook) - auto-compounds as permanently locked pool liquidity",
     "documented", 0.00285),
    ("Bankr protocol fee (hook)",
     "documented", 0.00475),
    ("BNKR buyback (hook) - buybacks + protocol-owned BNKR liquidity",
     "documented", 0.002375),
    ("Protocol / Doppler (hook)",
     "documented ~", 0.000875),
]
TOTAL_FEE = 0.0175  # 1.75% all-in, per the docs
CREATOR_SIDE = 0.0095  # 0.665% + 0.285% = 0.95% of volume

# Public RPC endpoints, tried in order until one answers with the right chain id.
DEFAULT_RPCS = {
    4663: [  # Robinhood Chain
        "https://rpc.mainnet.chain.robinhood.com",
        "https://robinhood-rpc.publicnode.com",
        "https://lb.routeme.sh/rpc/evm/4663",
        "https://rpc.robinhoodchain.io",
    ],
    8453: [  # Base
        "https://mainnet.base.org",
        "https://base-rpc.publicnode.com",
    ],
}

# ERC-20 selectors.
SEL_NAME = "06fdde03"
SEL_SYMBOL = "95d89b41"
SEL_DECIMALS = "313ce567"
SEL_TOTAL_SUPPLY = "18160ddd"


class RpcError(Exception):
    pass


def rpc_call(url, method, params, timeout=15):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method,
                       "params": params}).encode()
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json",
                 "User-Agent": "bankr-fee-walk/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RpcError("HTTP %s from %s" % (e.code, url))
    except Exception as e:
        raise RpcError("%s: %s" % (type(e).__name__, e))
    if "error" in payload:
        raise RpcError("RPC error: %s" % payload["error"])
    return payload.get("result")


def pick_rpc(chain_id, override=None):
    candidates = [override] if override else DEFAULT_RPCS.get(chain_id, [])
    if not candidates:
        raise RpcError("no known public RPC for chain id %d; pass --rpc" % chain_id)
    want = hex(chain_id)
    errors = []
    for url in candidates:
        try:
            got = rpc_call(url, "eth_chainId", [])
            if got == want or int(got, 16) == chain_id:
                return url
            errors.append("%s answered chain %s" % (url, got))
        except RpcError as e:
            errors.append("%s failed: %s" % (url, e))
    raise RpcError("no working RPC for chain %d:\n  %s"
                   % (chain_id, "\n  ".join(errors)))


def eth_call(url, to_addr, data):
    return rpc_call(url, "eth_call",
                    [{"to": to_addr, "data": "0x" + data}, "latest"])


def decode_string(hexdata):
    """Decode an ABI string return, falling back to bytes32."""
    raw = bytes.fromhex(hexdata[2:] if hexdata.startswith("0x") else hexdata)
    if len(raw) >= 64:
        offset = int.from_bytes(raw[0:32], "big")
        length = int.from_bytes(raw[32:64], "big")
        if offset == 32 and length <= len(raw) - 64:
            return raw[64:64 + length].decode("utf-8", errors="replace")
    # bytes32 fallback
    return raw[:32].split(b"\x00")[0].decode("utf-8", errors="replace")


def find_implementation(url, code_bytes):
    """Scan 20-byte windows of proxy bytecode for an address that holds code."""
    impls = []
    for i in range(len(code_bytes) - 19):
        candidate = "0x" + code_bytes[i:i + 20].hex()
        if candidate in impls:
            continue
        try:
            target_code = rpc_call(url, "eth_getCode", [candidate, "latest"])
        except RpcError:
            continue
        if target_code and target_code not in ("0x", "0x0"):
            impls.append(candidate)
    return impls


def main():
    ap = argparse.ArgumentParser(
        description="Re-derive a Bankr-launched token's expected fee split "
                    "from onchain reads.")
    ap.add_argument("address", help="token contract address (0x...)")
    ap.add_argument("--chain", type=int, default=4663,
                    help="chain id (default 4663, Robinhood Chain)")
    ap.add_argument("--rpc", default=None,
                    help="override RPC endpoint URL")
    ap.add_argument("--volume", type=float, default=10000.0,
                    help="sample trading volume in USD for the worked math "
                         "(default 10000)")
    args = ap.parse_args()

    addr = args.address
    if not (addr.startswith("0x") and len(addr) == 42):
        sys.exit("error: address must be a 0x-prefixed 42-character hex string")

    try:
        url = pick_rpc(args.chain, args.rpc)
    except RpcError as e:
        sys.exit("error: %s" % e)
    print("RPC: %s (chain id %d)\n" % (url, args.chain))

    # --- contract reads ---
    code = rpc_call(url, "eth_getCode", [addr, "latest"])
    code_bytes = bytes.fromhex(code[2:]) if code.startswith("0x") else bytes.fromhex(code)
    print("Contract: %s" % addr)
    print("Deployed bytecode: %d bytes" % len(code_bytes))
    if len(code_bytes) == 44:
        print("Classification: Bankr minimal proxy (44-byte proxy contract)")
        impls = find_implementation(url, code_bytes)
        if impls:
            print("Implementation address(es) with deployed code:")
            for impl in impls:
                print("  %s" % impl)
        else:
            print("Implementation: none found by bytecode scan")
    elif len(code_bytes) == 0:
        sys.exit("error: no contract deployed at %s on chain %d" % (addr, args.chain))
    else:
        print("Classification: full contract (%d bytes, not a minimal proxy)"
              % len(code_bytes))

    try:
        name = decode_string(eth_call(url, addr, SEL_NAME))
        symbol = decode_string(eth_call(url, addr, SEL_SYMBOL))
        decimals = int(eth_call(url, addr, SEL_DECIMALS), 16)
        total_raw = int(eth_call(url, addr, SEL_TOTAL_SUPPLY), 16)
    except RpcError as e:
        sys.exit("error reading token metadata: %s" % e)

    print("Name: %s" % name)
    print("Symbol: %s" % symbol)
    print("Decimals: %d" % decimals)
    print("Total supply: %s (%s raw units)"
          % ("{:,.0f}".format(total_raw / 10 ** decimals), format(total_raw, ",")))

    # --- documented fee split, with the math shown ---
    print("\nDocumented Bankr fee schedule (shares of trading volume):")
    print("  Source: https://docs.bankr.bot/llms-full.txt, verified 2026-09-24.")
    print("  Fixed at launch; existing tokens keep the schedule they launched with.\n")
    total = 0.0
    for label, derivation, share in FEE_ROWS:
        total += share
        usd = args.volume * share
        print("  %-62s %7.4f%%  ($%9.2f per $%s volume)  [%s]"
              % (label, share * 100, usd,
                 format(args.volume, ",.0f"), derivation))
    print("  %-62s %7.4f%%" % ("TOTAL", total * 100))
    assert abs(total - TOTAL_FEE) < 1e-9, "fee rows do not sum to 1.75%"
    print("\n  Creator side (claimable + locked compounding): %.3f%% of volume"
          % (CREATOR_SIDE * 100))
    print("  Of that, claimable by the creator: 0.665%; the 0.285% LP share")
    print("  auto-compounds as locked pool liquidity and is not spendable.")
    print("\nNote: quote-only vs mixed fee mode and the actual fee recipient are")
    print("set at launch and are not readable from these calls. This table shows")
    print("the documented schedule, not live fee state.")


if __name__ == "__main__":
    main()
