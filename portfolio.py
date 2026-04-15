"""
Portfolio data management and API calls for My Bitcoin World.

Storage: ~/.config/MyBitcoinWorld/portfolio.json
API:
  - Balances: https://blockstream.info/api/address/{addr}
  - BTC/USD:  https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime


# --- Storage path ---
def get_portfolio_path():
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    config_dir = os.path.join(base, "MyBitcoinWorld")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "portfolio.json")


# --- Load / Save ---
def load_portfolio() -> dict:
    """
    Returns dict:
    {
      "addresses": [
        {
          "address": "bc1q...",
          "label": "My cold wallet",
          "balance_btc": 0.5,
          "last_updated": "2024-01-01 12:00:00"
        }, ...
      ],
      "btc_usd": 65000.0,
      "btc_usd_updated": "2024-01-01 12:00:00"
    }
    """
    try:
        with open(get_portfolio_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"addresses": [], "btc_usd": None, "btc_usd_updated": None}


def save_portfolio(data: dict):
    with open(get_portfolio_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# --- API calls ---
TIMEOUT = 10

def _fetch_json(url: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; MyBitcoinWorld/1.0)",
        "Accept": "application/json",
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_btc_price() -> tuple:
    """
    Returns (price_usd: float, error: str|None).
    Tries multiple sources in order.
    """
    sources = [
        # Blockchain.info - simple, reliable
        ("https://blockchain.info/ticker",
         lambda d: float(d["USD"]["last"])),
        # CoinGecko
        ("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
         lambda d: float(d["bitcoin"]["usd"])),
        # Mempool.space
        ("https://mempool.space/api/v1/prices",
         lambda d: float(d["USD"])),
    ]
    last_err = "Unknown error"
    for url, extractor in sources:
        try:
            data = _fetch_json(url)
            price = extractor(data)
            return price, None
        except Exception as e:
            last_err = str(e)
            continue
    return None, last_err


def fetch_address_balance(address: str) -> tuple:
    """
    Returns (balance_btc: float, error: str|None)
    Uses Blockstream API - no key needed, very high limits.
    Balance = confirmed + unconfirmed funded - spent
    """
    try:
        url = f"https://blockstream.info/api/address/{address}"
        data = _fetch_json(url)
        chain = data.get("chain_stats", {})
        mempool = data.get("mempool_stats", {})
        funded = chain.get("funded_txo_sum", 0) + mempool.get("funded_txo_sum", 0)
        spent  = chain.get("spent_txo_sum",  0) + mempool.get("spent_txo_sum",  0)
        balance_sat = funded - spent
        balance_btc = balance_sat / 1e8
        return balance_btc, None
    except urllib.error.URLError as e:
        return None, f"Network error: {e.reason}"
    except Exception as e:
        return None, str(e)


def refresh_all(portfolio: dict, progress_cb=None) -> tuple:
    """
    Fetches fresh BTC price and all address balances.
    progress_cb(current, total, address) called for each step.
    Returns (updated_portfolio, errors: list[str])
    """
    errors = []
    total = len(portfolio["addresses"]) + 1  # +1 for price

    # Fetch BTC price
    if progress_cb:
        progress_cb(0, total, "BTC/USD price")
    price, err = fetch_btc_price()
    if err:
        errors.append(f"BTC price: {err}")
    else:
        portfolio["btc_usd"] = price
        portfolio["btc_usd_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Fetch each address
    for i, entry in enumerate(portfolio["addresses"]):
        addr = entry["address"]
        if progress_cb:
            progress_cb(i + 1, total, addr)
        balance, err = fetch_address_balance(addr)
        if err:
            errors.append(f"{addr[:16]}...: {err}")
        else:
            entry["balance_btc"] = balance
            entry["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    return portfolio, errors


# --- Address management ---
def add_address(portfolio: dict, address: str, label: str) -> tuple:
    """
    Adds address to portfolio. Returns (portfolio, error|None).
    Checks for duplicates.
    """
    address = address.strip()
    label = label.strip()

    if not address:
        return portfolio, "empty_address"

    # Basic BTC address validation (starts with 1, 3, or bc1)
    if not (address.startswith("1") or address.startswith("3") or
            address.lower().startswith("bc1")):
        return portfolio, "invalid_address"

    if len(address) < 26 or len(address) > 90:
        return portfolio, "invalid_address"

    # Check duplicate
    for entry in portfolio["addresses"]:
        if entry["address"] == address:
            return portfolio, "duplicate_address"

    portfolio["addresses"].append({
        "address": address,
        "label": label or address[:12] + "...",
        "balance_btc": None,
        "last_updated": None
    })
    return portfolio, None


def remove_address(portfolio: dict, address: str) -> dict:
    portfolio["addresses"] = [
        e for e in portfolio["addresses"] if e["address"] != address
    ]
    return portfolio


def update_label(portfolio: dict, address: str, new_label: str) -> dict:
    for entry in portfolio["addresses"]:
        if entry["address"] == address:
            entry["label"] = new_label.strip()
            break
    return portfolio


def total_btc(portfolio: dict) -> float:
    total = 0.0
    for e in portfolio["addresses"]:
        if e.get("balance_btc") is not None:
            total += e["balance_btc"]
    return total
