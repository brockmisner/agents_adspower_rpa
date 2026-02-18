"""
Ultimate Polymarket Forecasting System

Syntax-fixed scaffold focused on the issues in the provided file:
- Corrected method indentation for `_poll_clob_prices`
- Added missing `get_prices()` accessor used by the engine
"""

from __future__ import annotations

import json
import logging
import os
import ssl
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional

import requests
import websocket

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class TradingSignal:
    timestamp: datetime
    action: str


class PolymarketWebSocket:
    def __init__(self) -> None:
        self.ws = None
        self.running = False

        self.market_id = None
        self.condition_id_up = None
        self.condition_id_down = None
        self.market_end_time = None

        self.up_price = None
        self.down_price = None
        self.up_bid = None
        self.up_ask = None
        self.down_bid = None
        self.down_ask = None
        self.last_update = None

        self.recording_enabled = True
        self.data_dir = "data"
        self.record_file_path = None
        os.makedirs(self.data_dir, exist_ok=True)

        self.btc_price = None
        self.open_price = None

    def connect(self) -> bool:
        def on_open(ws):
            logger.info("✓ Polymarket CLOB WebSocket connected")

        def on_message(ws, message):
            _ = ws
            _ = message

        def on_error(ws, error):
            _ = ws
            logger.error("Polymarket WS error: %s", error)

        def on_close(ws, close_status_code, close_msg):
            _ = ws
            _ = close_msg
            logger.warning("Polymarket WS closed: %s", close_status_code)

        self.ws = websocket.WebSocketApp(
            "wss://ws-subscriptions-clob.polymarket.com/ws/market",
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )

        self.running = True
        threading.Thread(
            target=lambda: self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE}), daemon=True
        ).start()
        threading.Thread(target=self._poll_clob_prices, daemon=True).start()
        return True

    def _poll_clob_prices(self) -> None:
        """Poll CLOB REST prices continuously (syntax-fixed indentation)."""
        clob_base = "https://clob.polymarket.com"
        round_seconds = 300.0

        while self.running:
            try:
                up_bid = up_ask = down_bid = down_ask = None

                if self.condition_id_up:
                    r_bid = requests.get(
                        f"{clob_base}/price",
                        params={"token_id": self.condition_id_up, "side": "BUY"},
                        timeout=5,
                    )
                    r_ask = requests.get(
                        f"{clob_base}/price",
                        params={"token_id": self.condition_id_up, "side": "SELL"},
                        timeout=5,
                    )
                    if r_bid.status_code == 200:
                        up_bid = float(r_bid.json().get("price") or 0) or None
                    if r_ask.status_code == 200:
                        up_ask = float(r_ask.json().get("price") or 0) or None

                if self.condition_id_down:
                    r_bid = requests.get(
                        f"{clob_base}/price",
                        params={"token_id": self.condition_id_down, "side": "BUY"},
                        timeout=5,
                    )
                    r_ask = requests.get(
                        f"{clob_base}/price",
                        params={"token_id": self.condition_id_down, "side": "SELL"},
                        timeout=5,
                    )
                    if r_bid.status_code == 200:
                        down_bid = float(r_bid.json().get("price") or 0) or None
                    if r_ask.status_code == 200:
                        down_ask = float(r_ask.json().get("price") or 0) or None

                if up_bid is not None and up_ask is not None and up_bid > up_ask:
                    up_bid, up_ask = up_ask, up_bid
                if down_bid is not None and down_ask is not None and down_bid > down_ask:
                    down_bid, down_ask = down_ask, down_bid

                self.up_bid, self.up_ask = up_bid, up_ask
                self.down_bid, self.down_ask = down_bid, down_ask
                self.up_price = (up_bid + up_ask) / 2 if up_bid is not None and up_ask is not None else None
                self.down_price = (
                    (down_bid + down_ask) / 2 if down_bid is not None and down_ask is not None else None
                )
                self.last_update = datetime.now(timezone.utc)

                if self.recording_enabled and self.record_file_path and self.market_end_time:
                    if None not in (up_bid, up_ask, down_bid, down_ask):
                        now_ts = time.time()
                        end_ts = self.market_end_time.timestamp()
                        remaining = max(0.0, end_ts - now_ts)
                        progress = 1.0 - (remaining / round_seconds)
                        row = {
                            "ts": int(now_ts * 1000),
                            "dt": datetime.now(timezone.utc).isoformat(),
                            "up_bid": up_bid,
                            "up_ask": up_ask,
                            "down_bid": down_bid,
                            "down_ask": down_ask,
                            "sec_remaining": round(remaining, 3),
                            "progress": round(progress, 6),
                            "market_id": self.market_id,
                            "up_token": self.condition_id_up,
                            "down_token": self.condition_id_down,
                            "btc_price": self.btc_price,
                            "open_price": self.open_price,
                        }
                        with open(self.record_file_path, "a", encoding="utf-8") as f:
                            f.write(json.dumps(row) + "\n")

            except Exception as exc:  # noqa: BLE001
                logger.error("CLOB price poll error: %s", exc)

            time.sleep(0.5)

    def get_prices(self) -> Optional[Dict[str, Optional[float]]]:
        if self.up_price is None or self.down_price is None:
            return None
        return {
            "up_price": self.up_price,
            "down_price": self.down_price,
            "up_bid": self.up_bid,
            "up_ask": self.up_ask,
            "down_bid": self.down_bid,
            "down_ask": self.down_ask,
        }

    def stop(self) -> None:
        self.running = False
        if self.ws:
            self.ws.close()


if __name__ == "__main__":
    logger.info("Syntax-fixed module loaded successfully.")
